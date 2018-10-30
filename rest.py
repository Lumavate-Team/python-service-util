from flask import request, abort, g, Blueprint, send_from_directory
from .request import api_response, SecurityType
from app import rest_model_mapping
from app import db
import re
import os

camel_pat = re.compile(r'([A-Z0-9])')
under_pat = re.compile(r'_([A-Za-z0-9])')
hyphen_pat = re.compile(r'-([A-Za-z0-9])')

def hyphen_to_camel(name):
	return hyphen_pat.sub(lambda x: x.group(1).upper(), name)

def underscore_to_camel(name):
	return under_pat.sub(lambda x: x.group(1).upper(), name)

def camel_to_underscore(name):
	return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)

def make_id(id, classification):
  if hasattr(classification, '__table__'):
    return os.environ.get('WIDGET_URL_PREFIX').strip('/').replace('/', '~') + '!' + classification.__table__.name + '!' + str(id)
  else:
    return os.environ.get('WIDGET_URL_PREFIX').strip('/').replace('/', '~') + '!' + classification + '!' + str(id)

class RestBehavior:
  def __init__(self, model_class):
    self._model_class = model_class

  def get_org_id(self):
    return g.org_id

  def create_record(self, for_model):
    r = for_model()
    db.session.add(r)
    if hasattr(r, 'org_id'):
      r.org_id = self.get_org_id()

    if hasattr(r, 'created_by'):
      r.created_by = g.auth_status.get('user')

    if hasattr(r, 'last_modified_by'):
      r.last_modified_by = g.auth_status.get('user')

    return r

  def apply_filter(self, q):
    for a in request.args:
      if hasattr(self._model_class, camel_to_underscore(a)):
        q = q.filter(getattr(self._model_class, camel_to_underscore(a)) == request.args[a])
    return q

  def get_collection(self):
    if self._model_class is None:
      return None

    q = self._model_class.get_all()

    return self.apply_filter(q)

  def read_value(self, data, field_name):
    return data.get(field_name)

  def apply_values(self, rec):
    payload = rec.to_json()
    data = request.get_json(force=True)

    if hasattr(rec, 'last_modified_by'):
      rec.last_modified_by = g.auth_status.get('user')

    for k in payload:
      if k in data:
        setattr(rec, camel_to_underscore(k), self.read_value(data, k))

  def validate(self, rec):
    db.session.flush()
    required = [col.name for col in self._model_class.__table__.columns if not col.nullable if col.name != 'id']
    for r in required:
      if getattr(rec, r) is None:
        abort(400, 'required: ' + r)

  def post(self):
    rec = self.create_record(self._model_class)
    self.apply_values(rec)
    self.validate(rec)

    return rec

  def get_id(self, id):
    if isinstance(id, int):
      return id

    if id.isdigit():
      return id
    else:
      try:
        object_type = self._model_class.__table__.name
        service, object, id = id.split('!')
        if object_type != object:
          return None

        return int(id)
      except:
        return None

  def get_single(self, record_id):
    record_id = self.get_id(record_id)
    return self.apply_filter(self._model_class.get_all()).filter(self._model_class.id == record_id).first()

  def put(self, record_id):
    record_id = self.get_id(record_id)
    r = self._model_class.get(record_id)
    if r is not None:
      self.apply_values(r)
      self.validate(r)

    return r

  def delete(self, record_id):
    record_id = self.get_id(record_id)
    r = self._model_class.get(record_id)
    result = None
    if r is not None:
      db.session.delete(r)
      result = r.to_json()

    return result


rest_blueprint = Blueprint('rest_blueprint', __name__)
icon_blueprint = Blueprint('icon_blueprint', __name__)

@icon_blueprint.route("/<string:integration_cloud>/<string:widget_type>/discover/icons/<string:icon>", methods=["GET", "OPTIONS"])
def icon(integration_cloud, widget_type, icon):
  response = send_from_directory('icons', icon)

  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  response.headers.add('Access-Control-Allow-Credentials', 'true')
  return response

@rest_blueprint.route('/<string:integration_cloud>/<string:widget_type>/<string:model_name>', methods=['GET', 'POST'])
@api_response(SecurityType.browser_origin)
def rest_collection(integration_cloud, widget_type, model_name):
  if request.method == 'POST':
    return rest_model_mapping.get(model_name, RestBehavior(None)).post()
  else:
    return rest_model_mapping.get(model_name, RestBehavior(None)).get_collection()

@rest_blueprint.route('/<string:integration_cloud>/<string:widget_type>/<string:model_name>/<int:record_id>', methods=['GET'])
@api_response(SecurityType.browser_origin)
def rest_single(integration_cloud, widget_type, model_name, record_id):
  if request.method == 'GET':
    return rest_model_mapping.get(model_name, RestBehavior(None)).get_single(record_id)
