from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from sqlalchemy import or_, cast, VARCHAR, func
from datetime import datetime
import os
import re
import json
from lumavate_properties import Properties, Components
from lumavate_exceptions import ValidationException, ApiException
from app import db
from ..rest import RestBehavior, camel_to_underscore, underscore_to_camel
from ..request import LumavateRequest
from ..resolver import Resolver
from ..paging import Paging
from ..name_sort import NameSort
from .asset_model import AssetBaseModel

class AssetRestBehavior(RestBehavior):
  def __init__(self, model_class=AssetBaseModel, data=None):
    super().__init__(model_class, data)

  def apply_sort(self, q):
    return NameSort().apply(q)

  def get_preview(self, asset_id):
    # implemented at the child class
    raise ApiException(400, 'Not Implemented')

  def make_user_id(self, id):
    return f'lmvt!{id}'

  def get_default_user_id(self):
    return 'lmvt!-1'

  def post(self):
    asset_data = self.get_data()
    self.validate_asset_name(asset_data)

    post_data = {
      'name': asset_data.get('assetName'),
      'orgId': self.get_org_id(),
      'isActive': True,
      'data': asset_data,
      'dependencyAssets': self.get_dependencies(asset_data)
    }

    self.data = post_data
    return super().post()

  def put(self, record_id):
    asset_update_data = self.get_data()
    asset_data = asset_update_data.get('data', {})
    asset_rec = self._model_class.get(record_id)

    self.validate_asset_name(asset_data, record_id)
    self.data = asset_update_data
    if 'assetName' in asset_data:
      self.data['name'] = asset_data['assetName']

    self.data['dependencyAssets'] = self.get_dependencies(asset_data)

    response_data = super().put(record_id)
    asset_response = {
      'state': asset_update_data.get('state'),
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
    if dependencies is None:
      return []

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
    asset_data = asset_data
    dependencies = [] if dependencies is None else dependencies

    if isinstance(asset_data, list):
      return [self._get_nested_dependencies(x, dependencies) for x in asset_data]

    elif isinstance(asset_data, dict):
      component_data = {}

      for k, v in asset_data.items():
        if isinstance(v, list) and k != 'componentTemplate':
          dependencies.extend([self._get_nested_dependencies(x, dependencies) for x in v])

        elif isinstance(v, dict):
          assetRef = v.get('assetRef',None)
          if assetRef and isinstance(assetRef, dict) \
            and 'assetId' in assetRef and 'containerId' in assetRef:

            dependencies.append({
              'assetId': assetRef['assetId'],
              'containerId': assetRef['containerId']
            })

    if len(dependencies)==0:
      return

    return dependencies


