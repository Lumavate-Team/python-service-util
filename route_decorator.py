from flask import abort, jsonify, request, g, Blueprint
from functools import wraps
from flask_sqlalchemy import BaseQuery
from .paging import Paging
from app import db
from base64 import b64decode
from lumavate_exceptions import ApiException
import json
from .security_type import SecurityType
from .request import get_lumavate_request
import re
import os

lumavate_blueprint = Blueprint('lumavate_blueprint', __name__)
all_routes = []

def __authenticate(security_type):
  jwt = get_lumavate_request().get_token(request.headers, 'Authorization')
  if jwt is None or jwt.strip() == '':
    jwt = get_lumavate_request().get_token(request.cookies, 'pwa_jwt')

  header, payload, signature = jwt.replace('Bearer ', '').split('.')
  token_data = json.loads(b64decode(payload + '==').decode('utf-8'))
  g.pwa_jwt = jwt.replace('Bearer ', '')
  g.token_data = token_data
  g.org_id = token_data.get('orgId')

  try:

    if request.path == os.environ.get('WIDGET_URL_PREFIX') + 'status' and request.method == 'POST':
      service_data = request.get_json(True)
    else:
      service_data = get_lumavate_request().get_service_data(request.headers.get('Lumavate-sut'))

    g.service_data = service_data['serviceData']
    g.session = service_data['session'] if service_data['session'] is not None else {}
    if 'authData' not in service_data:
      g.auth_status = get_lumavate_request().get_auth_status()
    else:
      g.auth_status = service_data.get('authData')
      if g.auth_status is None:
        g.auth_status = {
          'status': 'inactive',
          'roles': [],
          'user': 'anonymous'
        }

    g.activation_data = service_data.get('activationData') if service_data.get('activationData') is not None else {}

  except ApiException as e:
    if e.status_code == 404 and security_type == SecurityType.system_origin:
      g.service_data = {}
      g.session = {}
      g.auth_status = {
        'status': 'inactive',
        'roles': [],
        'user': 'anonymous'
      }
    else:
      raise



@lumavate_blueprint.route('/<string:integration_cloud>/<string:widget_type>/discover/health', methods=['GET', 'POST'])
def health(integration_cloud, widget_type):
  return jsonify({'status': 'Ok'})

@lumavate_blueprint.route('/<string:integration_cloud>/<string:widget_type>/discover/routes', methods=['GET'])
def allowed_routes(integration_cloud, widget_type):
  return jsonify(all_routes)

def lumavate_route(path, methods, request_type, security_types, required_roles=[]):
  def actual_decorator(f):
    @wraps(f)
    def wrapped(integration_cloud, widget_type, *args, **kwargs):
      g.integration_cloud = integration_cloud
      g.widget_type = widget_type

      try:
        __authenticate(request_type)
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

    lumavate_blueprint.add_url_rule(
      '/<string:integration_cloud>/<string:widget_type>' + path,
      endpoint=f.__name__,
      view_func=wrapped,
      methods=methods)

    regex_path = path.replace('-', '[-]')

    regex_path = re.sub('<string[^>]*>','[^/]*', regex_path)
    regex_path = re.sub('<any[^>]*>','[^/]*', regex_path)
    regex_path = re.sub('<int[^>]*>','[0-9-]*', regex_path)

    all_routes.append({
      'path': '^' + regex_path + '$',
      'security': [x.name for x in security_types],
      'type': request_type.name
    })
    return wrapped
  return actual_decorator
