from flask import abort, jsonify, request, g, redirect, make_response
from functools import wraps
from flask_sqlalchemy import BaseQuery
from .paging import Paging
from lumavate_signer import Signer
from app import db
from base64 import b64decode
from lumavate_request import ApiRequest
from lumavate_exceptions import ApiException
import requests
import json
import os
import re

def __authenticate(storage, key, check_sut):
  valid_header = False
  if key in storage:
    try:
      jwt = storage.get(key)
      header, payload, signature = jwt.replace('Bearer ', '').split('.')
      token_data = json.loads(b64decode(payload + '==').decode('utf-8'))
      g.pwa_jwt = jwt.replace('Bearer ', '')
      g.token_data = token_data
      g.org_id = token_data.get('orgId')
      sut = None
      if check_sut:
        sut = request.headers.get('Lumavate-sut')
        if sut is None:
          sut = '--'

      if re.match(str(g.token_data.get('code')) + '[\.\_\-]', request.host) is None:
        raise Exception('Not Authorized')

      service_data = LumavateRequest().get_service_data(sut)
      g.service_data = service_data['serviceData']
      g.session = service_data['session']
      if service_data.get('sutValid', True) == False:
        raise Exception('Not Authorized')

    except Exception as e:
      raise Exception('Not Authorized')

    valid_header = True

  if valid_header == False:
    raise Exception('Not Authorized')

def api_response(check_sut=True, check_signature=False, required_roles=[]):
  def actual_decorator(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
      try:
        __authenticate(request.headers, 'Authorization', check_sut)
      except:
        return make_response('Not Authenticated', 401)

      try:
        r = f(*args, **kwargs)
        db.session.commit()
      except ApiException as e:
        return jsonify(e.to_dict()), e.status_code
      except:
        raise
        abort(500)

      if r is None:
        abort(404)

      if isinstance(r, BaseQuery):
        return Paging().run(r)

      if hasattr(r, 'to_json'):
        return jsonify(r.to_json())

      if isinstance(r, dict):
        return jsonify(r)

      if isinstance(r, list):
        return jsonify({'payload': { 'data': r }})

    return wrapped
  return actual_decorator

def browser_response(f):
  @wraps(f)
  def wrapped(*args, **kwargs):
    try:
      __authenticate(request.cookies, 'pwa_jwt', False)
    except:
      return redirect('https://' + request.host + '?u=' + request.url.replace('http://', 'https://'), 302)

    try:
      print(request.url, flush=True)
      r = f(*args, **kwargs)
    except:
      raise

    return r
  return wrapped

class LumavateRequest(ApiRequest):
  def sign_url(self, method, path, payload, headers):
    signer = Signer(os.environ.get('PUBLIC_KEY'), os.environ.get('PRIVATE_KEY'))
    return signer.get_signed_url(method, path, payload, headers)

  def get_auth_token(self):
    return 'Bearer ' + str(g.pwa_jwt)

  def get_base_url(self):
    return 'https://' + request.host
    #return os.environ.get('BASE_URL')

  def get_service_data(self, sut):
    sut_qs = ''
    if sut is not None:
      sut_qs = '?sut=' + sut
    return self.get('/pwa/v1/service-instances/' + os.environ.get('SERVICE_NAME') + sut_qs)
