from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
import rollbar
import re
import json
from lumavate_properties import Properties, Components
from lumavate_exceptions import ValidationException, ApiException
from ...rest import RestBehavior
from ...request import LumavateRequest
from ...resolver import Resolver
from ...paging import Paging
from ...name_sort import NameSort
from ...aws import FileBehavior, AwsClient
from ..models import AssetBaseModel
from ...util import camel_to_underscore, underscore_to_camel

try:
  from app import db
except:
  db = None

class AssetRestBehavior(RestBehavior):
  def __init__(self, model_class=AssetBaseModel, data=None):
    super().__init__(model_class, data)

    # override to specify fields to filter out during clone if cloning
    self.copy_ignore_fields = []

  def apply_sort(self, q):
    return NameSort().apply(q)

  def get_preview(self, asset_id):
    # implemented at the child class
    raise ApiException(400, 'Not Implemented')

  def make_user_id(self, id):
    return f'lmvt!{id}'

  def get_default_user_id(self):
    return 'lmvt!-1'

  def get_asset_content(self, asset_id):
    #overridden in most cases
    return self.get(asset_id)

  def get_batch_asset_content(self):
    asset_ids = self.get_data()
    response = {}
    for id in asset_ids:
      response[id] = self.get_asset_content(id)

    return response

  def post(self):
    asset_data = self.get_data()
    self.validate_asset_name(asset_data)
    asset_data = self.update_file_tags(asset_data)
    post_data = self.get_post_data(asset_data)

    self.data = post_data
    return super().post()

  def get_post_data(self, asset_data):
    return {
      'name': asset_data.get('assetName'),
      'orgId': self.get_org_id(),
      'isActive': True,
      'data': asset_data,
      'dependencyAssets': self.get_dependencies(asset_data)
    }

  def clone(self):
    clone_request = self.get_data()
    parsed_result = self._parse_source_data(clone_request)
      
    self.data = parsed_result['data']
    new_asset = self.post()
    return {
      'data': new_asset, 
      'unmappedFields': parsed_result.get('unmappedFields', []) ,
      'updatedFields': parsed_result.get('updatedFields', [])
    }

  def put(self, record_id):
    asset_update_data = self.get_data()
    asset_data = asset_update_data.get('data', {})

    self.validate_asset_name(asset_data, record_id)
    asset_update_data['data'] = self.update_file_tags(asset_data)
    self.data = asset_update_data
    if 'assetName' in asset_data:
      self.data['name'] = asset_data['assetName']

    self.data['dependencyAssets'] = self.get_dependencies(asset_update_data)

    response_data = super().put(record_id)

    asset_response = {
      'state': asset_update_data.get('state', 'promoted'),
      'payload': response_data
    }
    return asset_response

  def validate_asset_name(self, property_data, record_id=None):
    if 'assetName' not in property_data:
      return

    existing_name_asset = self.get_collection_query() \
        .filter(func.lower(self._model_class.name) == func.lower(property_data.get('assetName'))).first()

    if existing_name_asset is not None and (record_id is None or existing_name_asset.id != record_id):
      raise ValidationException('Name is already taken.', 'assetName')

  def pack(self, rec):
    if rec is None:
      return {}

    if type(rec) is self._model_class:
      return rec.to_json()
    else:
      return {self.underscore_to_camel(key):value for(key,value) in rec._asdict().items()}

  def get_dependencies(self, asset_data):
    dependencies = self._get_nested_dependencies(asset_data)

    flattened = []
    for d in dependencies:
      if d is None:
        continue
      if isinstance(d, list):
        flattened.extend(d)
      if isinstance(d,dict):
        flattened.append(d)
    return flattened

  def _get_nested_dependencies(self, asset_data, dependencies=None):
    dependencies = [] if dependencies is None else dependencies

    if isinstance(asset_data, list):
      for x in asset_data:
        self._get_nested_dependencies(x, dependencies)

    elif isinstance(asset_data, dict):
      for k, v in asset_data.items():
        if k == 'componentTemplate' or not v or (not isinstance(v, dict) and not isinstance(v, list)):
          continue

        if k == 'assetRef' and isinstance(v, dict) and 'assetId' in v and 'containerId' in v:
          dependencies.append({
            'assetId': v['assetId'],
            'containerId': v['containerId']
          })
        else:
          self._get_nested_dependencies(v, dependencies)

    return dependencies

  def read_property_values(self, asset_data, properties=[]):
    if not asset_data:
      return {}

    for p in properties:
      prop = Properties.Property.from_json(p)
      values = {p['name']: asset_data.get(p['name'])}
      asset_data[prop.name] = prop.read(values)

    return asset_data

  def update_file_tags(self, data):
    if not data or not isinstance(data, dict):
      return data

    file_behavior = FileBehavior()
    for prop_name, prop_value in data.items():
      if isinstance(prop_value, dict) and 'ephemeralKey' in prop_value:
        file_behavior.update_file_tags(prop_value.get('ephemeralKey'))
        prop_value['path'] = prop_value['ephemeralKey']
        prop_value['url'] = AwsClient().objects.get_public_url(prop_value['ephemeralKey'])

        del prop_value['ephemeralKey']

    return data

  def _parse_source_data(self, clone_request):
    scrubbed_source_data = self._scrub_source_data(clone_request.get('sourceAsset'))

    return  self.map_source_to_target(scrubbed_source_data, clone_request.get('target',{}))

  # remove all source asset specific fields that are created or retrieved at create/get time
  # these are defined in overridden 
  def _scrub_source_data(self, source_asset_data):
    # these are specific to form, each asset might have their own fields to ignore
    ignore_fields = self.copy_ignore_fields if self.copy_ignore_fields is not None else []
    if not ignore_fields:
      return source_asset_data


    clean_source_data = {}
    for key, value in source_asset_data.items():
      if key in ignore_fields:
        continue

      clean_source_data[key] = value
      
    return clean_source_data
      
  # Override in python-service-util/asset services asset specific mapping as needed
  def map_source_to_target(self, source_data, target):
    mapped_data = source_data
    mapped_data['assetName'] = target['assetName']

    return {
      'data': mapped_data, 
      'unmappedFields': [], 
      'updatedFields': [] 
    }