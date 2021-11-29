from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from lumavate_properties import Properties, Components
from lumavate_exceptions import ValidationException, NotFoundException, ApiException
from sqlalchemy import or_, cast, VARCHAR, func
import itertools
from app import db
import os
import re
import json
from .asset_rest import AssetRestBehavior
from ..models import AssetBaseModel
from ..file_filter import FileFilter

class FileAssetRestBehavior(AssetRestBehavior):
  def __init__(self, model_class=AssetBaseModel, data=None):
    super().__init__(model_class, data)

  def get_asset_content(self, asset_id):
    return self._get_document_content(asset_id)

  def _get_document_content(self, record_id):
    asset = models.Asset.get(record_id)

    image = {}
    # Document Asset Type content response has not been finalized
    return {
      'url': image['url'],
      'filename': image['filename'],
      'filetype': image['filetype']
    }

  def apply_filter(self, q, ignore_fields=None):
    return FileFilter(self.args, ignore_fields).apply(q)

  def get_asset_properties(self):
    raise ApiException(500, "get asset properties not implemented")

  def post(self):
    asset_data = self.get_data()

    properties = self.get_asset_properties()
    self.data = self.read_property_values(asset_data, properties)
    return super().post()

  def put(self, record_id):
    asset_update_data = self.get_data()
    asset_data = asset_update_data.get('data', {})

    properties = self.get_asset_properties()
    asset_update_data['data'] = self.read_property_values(asset_data, properties)
    self.data = asset_update_data
    return super().put(record_id)

  def delete(self, record_id):
    # Delete s3 object
    return super().delete(record_id)
