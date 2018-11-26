from flask import abort, jsonify, request, g, redirect, make_response
from functools import wraps
from flask_sqlalchemy import BaseQuery
from .paging import Paging
from lumavate_signer import Signer
from app import app, db
from base64 import b64decode
from lumavate_request import ApiRequest
from lumavate_exceptions import ApiException, AuthorizationException
from enum import Enum
import requests
import json
import os
import re
from .security_type import SecurityType

def __authenticate(storage, key, security_type):
  if SecurityType.browser_origin == security_type:
    check_sut = False
    restrict_domain = True
  elif SecurityType.api_origin == security_type:
    check_sut = False
    restrict_domain = True
  elif SecurityType.system_origin == security_type:
    check_sut = False
    restrict_domain = False

  valid_header = False

  jwt = get_lumavate_request().get_token(storage, key)
  header, payload, signature = jwt.replace('Bearer ', '').split('.')
  token_data = json.loads(b64decode(payload + '==').decode('utf-8'))
  g.pwa_jwt = jwt.replace('Bearer ', '')
  g.token_data = token_data
  g.org_id = token_data.get('orgId')

  if (not os.environ.get('DEV_MODE', 'False').lower() == 'true') and restrict_domain == True:
    if re.match('(' + str(g.token_data.get('code')) + '|' + str(g.token_data.get('namespace')) + ')[._\-:]', request.host) is None:
      raise AuthorizationException('Domain mismatch')

  try:
    service_data = get_lumavate_request().get_service_data(request.headers.get('Lumavate-sut'))
    g.service_data = service_data['serviceData']
    g.session = service_data['session']
  except ApiException as e:
    if e.status_code == 404 and security_type == SecurityType.system_origin:
      g.service_data = {}
      g.session = {}
    else:
      raise

  if check_sut == True and service_data and service_data.get('sutValid', True) == False:
    raise Exception('Not Authorized')

  g.auth_status = get_lumavate_request().get_auth_status()
  valid_header = True

  if valid_header == False:
    raise Exception('Not Authorized')

def api_response(security_type, required_roles=[]):
  def actual_decorator(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
      try:
        __authenticate(request.headers, 'Authorization', security_type)
      except ApiException as e:
        return jsonify(e.to_dict()), e.status_code

      try:
        r = f(*args, **kwargs)
        db.session.commit()
      except ApiException as e:
        db.session.rollback()
        return jsonify(e.to_dict()), e.status_code
      except Exception as e:
        db.session.rollback()
        raise

      if r is None:
        abort(404)

      if isinstance(r, BaseQuery):
        return Paging().run(r)

      if hasattr(r, 'to_json'):
        return jsonify({'payload': {'data': r.to_json()}})

      if isinstance(r, dict):
        return jsonify({'payload': {'data': r}})

      if isinstance(r, list):
        return jsonify({'payload': { 'data': r }})

      return r

    return wrapped
  return actual_decorator

def browser_response(f):
  @wraps(f)
  def wrapped(*args, **kwargs):
    try:
      __authenticate(request.cookies, 'pwa_jwt', SecurityType.browser_origin)
    except:
      return redirect('https://' + request.host + '?u=' + request.url.replace('http://', 'https://'), 302)

    r = f(*args, **kwargs)

    return r
  return wrapped

alt_lumavate_request_factory = None

def set_lumavate_request_factory(func):
  global alt_lumavate_request_factory
  alt_lumavate_request_factory = func

def get_lumavate_request():
  if alt_lumavate_request_factory is None:
    return LumavateRequest()
  else:
    return alt_lumavate_request_factory()

class LumavateRequest(ApiRequest):
  def sign_url(self, method, path, payload, headers):
    signer = Signer(os.environ.get('PUBLIC_KEY'), os.environ.get('PRIVATE_KEY'))
    return signer.get_signed_url(method, path, payload, headers)

  def get_auth_token(self):
    return 'Bearer ' + str(g.pwa_jwt)

  def get_base_url(self):
    return '{}{}'.format(os.environ.get('PROTO'), request.host)

  def get_token(self, storage, key):
    return storage.get(key)

  def get_service_data(self, sut):
    sut_qs = ''
    if sut is not None:
      sut_qs = '?sut=' + sut
    d = self.get('/pwa/v1/service-instances/' + os.environ.get('SERVICE_NAME') + sut_qs)
    #with open('/app/service-data.json', 'w') as outfile:
    #  json.dump(d, outfile, sort_keys=True, indent=4)
    return d

  def make_request(
      self,
      method,
      path,
      headers=None,
      payload=None,
      files=None,
      raw=False,
      timeout=None):
    """Make a request with the given method and parameters"""
    response_content = None
    results = {}

    if headers is None:
      headers = {}

    if timeout is None:
      # If timeout is not set, requests library will hang indefinitely
      timeout = 30

    if 'Authorization' not in headers:
      headers['Authorization'] = self.get_auth_token()

    if 'Content-Type' not in headers:
      headers['Content-Type'] = 'application/json'

    if path.startswith('/'):
      if self.get_base_url.endswith('/'):
        path = self.get_base_url()[:-1] + path
      else:
        path = self.get_base_url() + path

    if payload is not None and isinstance(payload, dict):
      payload = json.dumps(payload)

    headers['Connection'] = 'close'

    with requests.Session() as session:
      url = self.sign_url(method, path, payload, headers)
      func = getattr(session, method.lower())
      res = func(
          url,
          headers=headers,
          data=payload,
          stream=True,
          timeout=timeout,
          files=files)

      res.encoding = 'utf-8' if not(res.encoding) else res.encoding

      for chunk in res.iter_content(chunk_size=524288, decode_unicode=not raw):
        if chunk:
          if response_content is None:
            response_content = chunk
          else:
            response_content += chunk

      if res.status_code == 200:
        if raw:
          results = response_content
        else:
          results = json.loads(response_content)
      else:
        results = response_content

    return self.handle_response(res, results, raw=raw)

  def handle_response(self, res, data=None, raw=False):
    """Given the request outcome, properly respond to the data"""
    response_data = data

    if res.status_code == 200:
      if not raw and 'payload' in response_data:
        return response_data['payload']['data']

      return response_data

    return self.raise_exception(res, response_data)

  def raise_exception(self, res, response_data):
    raise ApiException(
        res.status_code,
        'Error making request ' + res.url + ':' + res.request.method + ' - ' + str(res.status_code) + str(response_data))

  def get_auth_status(self):
    auth_status = {
      'status': 'inactive',
      'roles': [],
      'user': 'anonymous'
    }
    try:
      if g.token_data.get('authUrl') and str(g.token_data.get('authUrl')).strip('/').split('/')[-1] != os.environ.get('SERVICE_NAME'):
        if g.token_data.get('authUrl').startswith('http://'):
          auth_status = LumavateRequest().get(g.token_data.get('authUrl') + 'status')
        else:
          auth_status = LumavateRequest().get('{}{}{}'.format(self.get_base_url(), g.token_data.get('authUrl'), 'status'))
    except Exception as e:
      print(g.token_data.get('authUrl'), flush=True)
      print(e, flush=True)
      pass

    #with open('/app/auth-data.json', 'w') as outfile:
    #  json.dump(auth_status, outfile, sort_keys=True, indent=4)
    return auth_status

class LumavateMockRequest(LumavateRequest):
  def __init__(self, mock_service, mock_auth, mock_token, mock_func):
    self._mock_service = mock_service
    self._mock_auth = mock_auth
    self._mock_token = mock_token
    self._mock_func = mock_func

  def get_service_data(self, sut):
    return self._mock_service

  def get_auth_status(self):
    return self._mock_auth

  def get_token(self, storage, key):
    return self._mock_token

  def make_request(
      self,
      method,
      path,
      headers=None,
      payload=None,
      files=None,
      raw=False,
      timeout=None):
    result = None
    if self._mock_func is not None:
      result = self._mock_func(method, path, headers, payload, files, raw, timeout)

    if result is None:
      return super().make_request(method, path, headers, payload, files, raw, timeout)
    else:
      return result
