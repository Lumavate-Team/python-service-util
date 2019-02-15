from flask import abort, jsonify, request, g, Blueprint
from lumavate_exceptions import ApiException
from .request import get_lumavate_request
from flask_sqlalchemy import BaseQuery
from .request_type import RequestType
from base64 import b64decode
from functools import wraps
from .paging import Paging
import json
import re
import os
try:
  from app import db
except:
  db = None

if os.path.isdir("/app/templates"):
  lumavate_blueprint = Blueprint('lumavate_blueprint', __name__)
else:
  template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
  lumavate_blueprint = Blueprint('lumavate_blueprint', __name__, template_folder=template_folder)

all_routes = []

def __authenticate_manage(request_type, required_roles):
  jwt = get_lumavate_request().get_token(request.headers, 'Authorization')
  if jwt is None or jwt.strip() == '':
    jwt = get_lumavate_request().get_token(request.cookies, 'pwa_jwt')

  if not jwt:
    raise ApiException(401, 'Missing token')

  header, payload, signature = jwt.replace('Bearer ', '').split('.')
  token_data = json.loads(b64decode(payload + '==').decode('utf-8'))

  if token_data.get('scope') != 'ms-manage':
    raise ApiException(401, 'Invalid scope')

  g.pwa_jwt = jwt.replace('Bearer ', '')
  g.token_data = token_data
  g.org_id = token_data.get('orgId')
  role = token_data.get('role')

  if required_roles and role not in required_roles:
    raise ApiException(403, 'Invalid role')

  return

def __authenticate(request_type):
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

    g.activation_data = service_data.get('activationData', {})

  except ApiException as e:
    # Older services that use SecurityType.system_origin will have a value of 3 which matches RequestType.system value
    if e.status_code == 404 and request_type.value == RequestType.system.value:
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

def handle_request(func, auth_func, integration_cloud, widget_type, *args, **kwargs):
  g.integration_cloud = integration_cloud
  g.widget_type = widget_type

  try:
    auth_func()
  except ApiException as e:
    return jsonify(e.to_dict()), e.status_code

  try:
    r = func(*args, **kwargs)
    if db:
      db.session.commit()
  except ApiException as e:
    if db:
      db.session.rollback()
    return jsonify(e.to_dict()), e.status_code
  except Exception as e:
    if db:
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

def add_url_rule(func, wrapped, path, methods, request_type, security_types, is_manage=False):
  lumavate_blueprint.add_url_rule(
    '/<string:integration_cloud>/<string:widget_type>' + path,
    endpoint=func.__name__,
    view_func=wrapped,
    methods=methods)

  regex_path = path.replace('-', '[-]')

  regex_path = re.sub('<string[^>]*>','[^/]*', regex_path)
  regex_path = re.sub('<any[^>]*>','[^/]*', regex_path)
  regex_path = re.sub('<int[^>]*>','[0-9-]*', regex_path)

  all_routes.append({
    'path': '^' + regex_path + '$',
    'security': [x.name for x in security_types],
    'type': request_type.name,
    'isManage': str(is_manage).lower()
  })

def lumavate_manage_route(path, methods, request_type, security_types, template_folder=None, required_roles=None):
  def decorator(f):
    @wraps(f)
    def wrapper(integration_cloud, widget_type, *args, **kwargs):
      return handle_request(f, lambda: __authenticate_manage(request_type, required_roles), integration_cloud, widget_type, *args, **kwargs)

    # Prefix manage routes with /manage
    add_url_rule(f, wrapper, '/manage{}'.format(path), methods, request_type, security_types, is_manage=True)

    return wrapper
  return decorator

def lumavate_route(path, methods, request_type, security_types, required_roles=None):
  def decorator(f):
    @wraps(f)
    def wrapper(integration_cloud, widget_type, *args, **kwargs):
      return handle_request(f, lambda: __authenticate(request_type), integration_cloud, widget_type, *args, **kwargs)

    add_url_rule(f, wrapper, path, methods, request_type, security_types)

    return wrapper
  return decorator

