from flask import request, abort, g, Blueprint, send_from_directory
import sqlalchemy.sql.expression
from sqlalchemy import or_
from .request import api_response, SecurityType
from .paging import Paging
from app import rest_model_mapping
from lumavate_exceptions import ValidationException
import csv
from io import StringIO
import re
import os
import json

try:
  from app import db
except:
  db = None

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
  def __init__(self, model_class, data=None, args=None):
    self._model_class = model_class
    self.data = data
    self.args = args

  def get_data(self, override_data=None):
    if override_data:
      return override_data

    if self.data:
      return self.data

    return request.get_json(force=True)

  def get_args(self):
    if self.args:
      return self.args

    return request.args

  def hyphen_to_camel(self, name):
    return hyphen_to_camel(name)

  def underscore_to_camel(self, name):
    return underscore_to_camel(name)

  def camel_to_underscore(self, name):
    return camel_to_underscore(name)

  def get_org_id(self):
    return g.org_id

  def get_batch_import_content(self):
    j = []

    input_data = ''
    if 'file' in request.files:
      f = request.files['file']
      input_data = f.read().decode('utf-8')
    else:
      input_data = request.get_data().decode('utf-8')

    try:
      j = json.loads(input_data)
    except Exception as e:
      sio = StringIO(input_data)
      reader = csv.DictReader(sio)
      for row in reader:
        j.append(row)

    return j

  def create_record(self, for_model):
    if not db:
      raise Exception('Unable to create record without db context')

    r = for_model()
    db.session.add(r)
    if hasattr(r, 'org_id'):
      r.org_id = self.get_org_id()

    if hasattr(r, 'created_by'):
      r.created_by = g.auth_status.get('user')

    if hasattr(r, 'last_modified_by'):
      r.last_modified_by = g.auth_status.get('user')

    return r

  def apply_filter(self, q, ignore_fields=[]):
    for a in self.get_args():
      if a in ignore_fields:
        continue

      if hasattr(self._model_class, camel_to_underscore(a)):
        or_clauses = [ getattr(self._model_class, camel_to_underscore(a)) == self.resolve_value(v)  for v in self.get_args()[a].split('||')]
        q = q.filter(or_(*[c for c in or_clauses if c is not None]))
    return q

  def resolve_value(self, val):
    if '.' in val:
      temp = val.split('.')
      if len(temp) > 1 and temp[0] == 'activationData':
        activationData = g.activation_data
        for key in temp[1:]:
          activationData = activationData.get(key)
        return  activationData
    return val

  def apply_sort(self, q):
    if 'sort' in self.get_args():
      sort_key = self.get_args()['sort']
      sort_direction = 'asc'
      if ' ' in sort_key:
        sort_key, sort_direction = sort_key.split(' ', 1)

      sort_dir_func = getattr(sqlalchemy.sql.expression, sort_direction)
      q = q.order_by(sort_dir_func(getattr(self._model_class, camel_to_underscore(sort_key))))
    return q

  def get_collection_query(self):
    if self._model_class is None:
      return None

    q = self._model_class.get_all()

    q = self.apply_filter(q)
    q = self.apply_sort(q)
    return q

  def get_collection(self):
    if self._model_class is None:
      return None

    q = self.get_collection_query()

    return Paging().run(q, self.pack)

  def read_value(self, data, field_name):
    return data.get(field_name)

  def apply_values(self, rec, data=None):
    payload = rec.to_json()
    data = self.get_data(data)
    updated_fields = []

    if hasattr(rec, 'last_modified_by'):
      rec.last_modified_by = g.auth_status.get('user')

    for k in payload:
      if k in ['id']:
        continue

      if k in data:
        if k in ['createdBy', 'createdAt', 'lastModifiedBy', 'lastModifiedAt']:
          continue

        if not hasattr(rec, camel_to_underscore(k)):
          continue

        if getattr(rec, camel_to_underscore(k)) != self.read_value(data, k):
          updated_fields.append(k)
        setattr(rec, camel_to_underscore(k), self.read_value(data, k))

    return updated_fields

  def validate(self, rec):
    if not db:
      raise Exception('Unable to validate record without db context')

    db.session.flush()
    required = [col.name for col in self._model_class.__table__.columns if not col.nullable if col.name != 'id']
    for r in required:
      if getattr(rec, r) is None or not str(getattr(rec, r)).strip():
        raise ValidationException('Field is Required', self.underscore_to_camel(r))

  def expanded(self, section):
    expand_sections = [a.strip() for a in self.get_args().get('expand', 'none').lower().split(',')]
    return section.lower() in expand_sections or 'all' in expand_sections

  def post(self):
    rec = self.create_record(self._model_class)
    self.apply_values(rec)
    self.validate(rec)

    return self.pack(rec)

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
    r = self.apply_filter(self._model_class.get_all()).filter(self._model_class.id == record_id).first()
    return self.pack(r)

  def put(self, record_id):
    record_id = self.get_id(record_id)
    r = self._model_class.get(record_id)
    if r is not None:
      self.apply_values(r)
      self.validate(r)

    return self.pack(r)

  def delete(self, record_id):
    if not db:
      raise Exception('Unable to validate record without db context')

    record_id = self.get_id(record_id)
    r = self._model_class.get(record_id)
    result = self.pack(r)

    if r is not None:
      db.session.delete(r)
      result = r.to_json()

    return result

  def pack(self, rec):
    if rec is None:
      return None

    return rec.to_json()


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
