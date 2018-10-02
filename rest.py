from flask import request, abort, g, Blueprint, send_from_directory
from .request import api_response, SecurityType
from app import rest_model_mapping
from app import db
import re

camel_pat = re.compile(r'([A-Z0-9])')
under_pat = re.compile(r'_([A-Za-z0-9])')
hyphen_pat = re.compile(r'-([A-Za-z0-9])')

def hyphen_to_camel(name):
	return hyphen_pat.sub(lambda x: x.group(1).upper(), name)

def underscore_to_camel(name):
	return under_pat.sub(lambda x: x.group(1).upper(), name)

def camel_to_underscore(name):
	return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)

class RestBehavior:
  def __init__(self, model_class):
    self.__model_class = model_class

  def get_org_id(self):
    return g.org_id

  def create_record(self, for_model):
    r = for_model()
    db.session.add(r)
    if hasattr(r, 'org_id'):
      r.org_id = self.get_org_id()

    return r

  def apply_filter(self, q):
    for a in request.args:
      if hasattr(self.__model_class, a):
        q = q.filter(getattr(self.__model_class, a) == request.args[a])
    return q

  def get_collection(self):
    if self.__model_class is None:
      return None

    q = self.__model_class.query
    if hasattr(self.__model_class, 'org_id'):
      q = q.filter(self.__model_class.org_id == g.token_data['orgId'])

    return self.apply_filter(q)

  def apply_values(self, rec):
    payload = rec.to_json()
    data = request.get_json(force=True)
    for k in payload:
      if k in data:
        setattr(rec, camel_to_underscore(k), data.get(k))

  def validate(self, rec):
    required = [col.name for col in self.__model_class.__table__.columns if not col.nullable if col.name != 'id']
    for r in required:
      if getattr(rec, r) is None:
        abort(400, 'required: ' + r)

  def post(self):
    rec = self.create_record(self.__model_class)
    self.apply_values(rec)
    self.validate(rec)

    return rec

  def get_single(self, record_id):
    return self.__model_class.query.filter(self.__model_class.id == record_id).first()


rest_blueprint = Blueprint('rest_blueprint', __name__)
icon_blueprint = Blueprint("qr_blueprint", __name__)

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
