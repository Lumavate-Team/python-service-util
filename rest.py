from flask import request, abort, g, Blueprint, send_from_directory
from datetime import datetime
import sqlalchemy.sql.expression
from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified
from .request import api_response, SecurityType
from .paging import Paging
from app import rest_model_mapping
from lumavate_exceptions import ValidationException
from sqlalchemy.schema import Sequence
from sqlalchemy.inspection import inspect
import csv
from io import StringIO
import re
import os
import json
from .column_select import ColumnSelect
from .filter import Filter
from .sort import Sort
from .asset_resolver import AssetResolver
from .util import hyphen_to_camel, camel_to_underscore, underscore_to_camel

try:
  from app import db
except:
  db = None

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
    self._asset_resolver = AssetResolver()

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

  def make_user_id(self, id):
    return id

  def get_default_user_id(self):
    return -1

  def create_record(self, for_model):
    if not db:
      raise Exception('Unable to create record without db context')


    r = for_model()
    db.session.add(r)
    if hasattr(r, 'org_id'):
      r.org_id = self.get_org_id()

    if hasattr(r, 'created_by'):
      user_id = g.auth_status.get('user')
      if not user_id:
        user_id = self.get_default_user_id()

      r.created_by = self.make_user_id(user_id)

    if hasattr(r, 'last_modified_by'):
      user_id = g.auth_status.get('user')
      if not user_id:
        user_id = self.get_default_user_id()

      r.last_modified_by = self.make_user_id(user_id)

    return r

  def apply_filter(self, q, ignore_fields=None):
    return Filter(self.args, ignore_fields).apply(q)

  def apply_select(self, q):
    return ColumnSelect(model_class=self._model_class, args=self.get_args()).apply(q)

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
    return Sort().apply(q)

  def get_collection_query(self):
    if self._model_class is None:
      return None

    q = self._model_class.get_all()

    q = self.apply_filter(q)
    q = self.apply_sort(q)
    q = self.apply_select(q)
    return q

  def get_collection(self):
    if self._model_class is None:
      return None

    q = self.get_collection_query()

    return Paging().run(q, self.pack)

  def read_value(self, data, field_name):
    return data.get(field_name)

  def rest_get_collection(self):
    return Paging().run(self.get_collection(), self.pack)

  def rest_get_single(self, id):
    return self.pack(self.get_single(id))

  def apply_values(self, rec, data=None):
    payload = rec.to_json()
    data = self.get_data(data)
    updated_fields = []

    if hasattr(rec, 'last_modified_by'):
      user_id = g.auth_status.get('user')
      if not user_id:
        user_id = self.get_default_user_id()

      rec.last_modified_by = self.make_user_id(user_id)

    if hasattr(rec, 'last_modified_at'):
      rec.last_modified_at = datetime.utcnow()

    for k in payload:
      if k in ['id']:
        continue

      if k in data:
        if k in self.get_ignored_properties():
          continue

        property_name = camel_to_underscore(k)
        if not hasattr(rec, property_name):
          continue

        if getattr(rec, property_name) != self.read_value(data, k):
          updated_fields.append(k)

        updated_value = self.read_value(data, k)
        if isinstance(data[k], dict):
          scrubbed_data = {key: value for (key,value) in data[k].items() if key not in self.get_ignored_properties()}

          updated_value = payload[k] if payload[k] is not None else {}
          updated_fields.append(k)
          updated_value.update(scrubbed_data)
          if payload['id'] is not None:
            flag_modified(rec, property_name)
          setattr(rec, property_name, updated_value)
        else:
          setattr(rec, property_name, self.read_value(data, k))

    return updated_fields

  def get_ignored_properties(self):
    return ['createdBy', 'createdAt', 'lastModifiedBy', 'lastModifiedAt']

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

  def read_from_request(self, obj, attributes, alt_input=None):
    for attribute in attributes:
      if hasattr(obj, attribute) or (hasattr(obj, 'set_' + attribute)):
        newVal = self.get_request_value(self.underscore_to_camel(attribute), alt_input=alt_input)
        if newVal is not None:
          if newVal == 'null': # this condition means a null was passed in, convert to None
            newVal = None

          if hasattr(obj, 'set_' + attribute) and callable(getattr(obj, 'set_' + attribute)):
            setMethod = getattr(obj, 'set_' + attribute)
            setMethod(newVal)
          else:
            setattr(obj, attribute, newVal)

  def get_next_sequence(self, name):
    return db.session.connection().execute(Sequence(name))

  def get_next_id(self, rec):
    sequence_name = inspect(rec.__class__).mapped_table.name + '_id_seq'
    return self.get_next_sequence(sequence_name)

  def rest_update_record(self, obj, attributes, alt_input=None):
    if obj is not None:
      self.read_from_request(obj, attributes, alt_input=alt_input)

      # Update base attributes
      if hasattr(obj, 'last_modified_by'):
        user_id = g.auth_status.get('user')
        if not user_id:
          user_id = self.get_default_user_id()

        obj.last_modified_by = self.make_user_id(user_id)

      if hasattr(obj, 'last_modified_at'):
        obj.last_modified_at = datetime.utcnow()

    return obj

  def rest_create_record(self, type, attributes, alt_input=None):
    obj = type()
    obj.id = self.get_next_id(obj)
    self.read_from_request(obj, attributes, alt_input=alt_input)

    # Update base attributes

    if hasattr(obj, 'last_modified_by'):
      user_id = g.auth_status.get('user')
      if not user_id:
        user_id = self.get_default_user_id()

      obj.last_modified_by = self.make_user_id(user_id)

    if hasattr(obj, 'last_modified_at'):
      obj.last_modified_at = datetime.utcnow()

    if hasattr(obj, 'created_by'):
      user_id = g.auth_status.get('user')
      if not user_id:
        user_id = self.get_default_user_id()

      obj.created_by = self.make_user_id(user_id)

    if hasattr(obj, 'created_at'):
      obj.created_at = datetime.utcnow()

    db.session.add(obj)
    return obj

  def get_request_value(self, value, alt_input=None):
    if alt_input is not None:
      return alt_input.get(value)

    json_data = request.get_json()
    if json_data is not None and value in json_data:
      return json_data.get(value)

    if value in request.form:
      return request.form[value]

    return None

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
    q = self.apply_filter(self._model_class.get_all()).filter(self._model_class.id == record_id)
    r = self.apply_select(q).first()
    return self.pack(r)

  def rest_create(self):
    return self.pack(self.create())

  def create(self):
    instance = self._model_class()
    attributes = instance.create_attributes if hasattr(instance, 'create_attributes') and len(instance.create_attributes) > 0 else instance.attributes
    rec = self.rest_create_record(self._model_class, attributes, alt_input=self.get_data())
    db.session.flush()
    rec = self.unpack(rec)
    db.session.flush()
    return rec

  def post(self):
    rec = self.create_record(self._model_class)
    self.apply_values(rec)
    self.validate(rec)
    return self.pack(rec)

  def rest_update(self, id):
    rec = self.update(self.get_single(id))
    return self.pack(rec)

  def update(self, rec):
    if rec is not None:
      attributes = rec.update_attributes if hasattr(rec, 'update_attributes') and len(rec.update_attributes) > 0 else rec.attributes
      rec = self.rest_update_record(rec, attributes, alt_input=self.get_data())
      db.session.flush()
      rec = self.unpack(rec)
      db.session.flush()

    return rec

  def put(self, record_id):
    record_id = self.get_id(record_id)
    rec = self._model_class.get(record_id)

    self.apply_values(rec)
    self.validate(rec)
    return self.pack(rec)

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
    if rec is not None:
      self.resolve_assets(rec)
      return rec.to_json()

  def unpack(self, rec):
    return rec

  def get_asset_fields(self):
    return []

  def resolve_assets(self, rec):
    for field in self.get_asset_fields():
      self.do_resolve(getattr(rec, field)) 

  def do_resolve(self, data, parent=None, parent_key=None):
    if not isinstance(data, dict):
      return
    
    if 'assetRef' in data:
      resolved_data = {}
      if data['assetRef']:
        resolved_data = self._asset_resolver.resolve(data['assetRef'])
    
      if self._asset_resolver.is_app_scope and parent and parent_key:
        parent[parent_key] = resolved_data
      elif data['assetRef']:
        data['assetRef']['asset'] = resolved_data
      else:
        data['assetRef'] = resolved_data
      return

    for key in data:
      if isinstance(data[key], dict):
        self.do_resolve(data[key], data, key)
      elif isinstance(data[key], list):
        for item in data[key]:
          self.do_resolve(item, data)
    


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
