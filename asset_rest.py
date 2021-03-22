from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from sqlalchemy import or_, cast, VARCHAR, func
import os
import re
import json
from lumavate_properties import Properties, Components
from lumavate_exceptions import ValidationException, ApiException
from app import db
from .rest import RestBehavior
from .request import LumavateRequest
from .resolver import Resolver
from .paging import Paging
from .asset_model import AssetBaseModel

class AssetRestBehavior(RestBehavior):
  def __init__(self, model_class=AssetBaseModel, data=None):
    super().__init__(model_class, data)

  def get_preview(self, asset_id):
    # implemented at the child class
    raise ApiException(400, 'Not Implemented')

  def post(self):
    asset_data = self.get_data()
    self.validate_asset_name(asset_data)

    asset_data = {
      'name': asset_data.get('assetName'),
      'orgId': self.get_org_id(),
      'isActive': True,
      'data': asset_data.get('data')
    }
    self.data = asset_data
    return super().post()

  def put(self, record_id):
    asset_update_data = self.get_data()
    asset_data = asset_update_data.get('data', {})
    asset_rec = self._model_class.get(record_id)

    self.validate_asset_name(asset_data, record_id)
    self.data = asset_update_data
    return super().put(record_id)

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

    return rec.to_json()
