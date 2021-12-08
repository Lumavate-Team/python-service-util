from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from lumavate_properties import Properties, Components
from lumavate_exceptions import ValidationException, NotFoundException, ApiException
from sqlalchemy import or_, cast, VARCHAR, func
import itertools
import rollbar
from app import db
import os
import re
import json
from .asset_rest import AssetRestBehavior
from ..models import FileAssetBaseModel
from ...aws import FileBehavior
from ..file_filter import FileFilter

class FileAssetRestBehavior(AssetRestBehavior):
  def __init__(self, model_class=FileAssetBaseModel, data=None):
    super().__init__(model_class, data)

  def get_asset_content(self, asset_id):
    asset = self._model_class.get(asset_id)
    return self._get_document_content(asset)

  def get_asset_content_by_public_id(self, public_id):
    asset = self._model_class.get_by_public_id(public_id)
    return self._get_document_content(asset)

  def _get_document_content(self, asset):
    if asset is None:
      return {}

    file = asset.data.get('file',{})
    image = {}
    # Document Asset Type content response has not been finalized
    return {
      'url': file['url'],
      'filename': file['filename'],
      'filetype': file['filetype'],
    }

  def apply_filter(self, q, ignore_fields=None):
    return FileFilter(self.args, ignore_fields).apply(q)

  def get_asset_properties(self):
    raise ApiException(500, "get asset properties not implemented")

  def post(self):
    asset_data = self.get_data()

    properties = self.get_asset_properties()
    asset_data = self.read_property_values(asset_data, properties)
    self.validate_asset_name(asset_data)
    asset_data = self.update_file_tags(asset_data)
    post_data = {
      'name': asset_data.get('assetName'),
      'orgId': self.get_org_id(),
      'isActive': True,
      'data': asset_data,
      'dependencyAssets': self.get_dependencies(asset_data)
    }
    filename = asset_data.get('file',{}).get('filename')
    # pull filename out into column for easy search query
    if filename:
      post_data['filename'] = filename

    self.data = post_data
    # skip asset rest since we already built up the post data
    return super(AssetRestBehavior, self).post()

  def put(self, record_id):
    record = self.get_single(record_id)
    original_path = record.get('data',{}).get('file',{}).get('path','')

    asset_update_data = self.get_data()
    asset_data = asset_update_data.get('data', {})

    properties = self.get_asset_properties()
    asset_update_data['data'] = self.read_property_values(asset_data, properties)
    file = asset_update_data['data'].get('file',{})

    # pull filename out into column for easy search query
    if file.get('filename'):
      asset_update_data['filename']=file['filename']

    self.data = asset_update_data
    response = super().put(record_id)

    # delete the old file when a new one is uploaded
    if file and file.get('ephemeralKey'):
      FileBehavior().delete(original_path)

    return response

  def delete(self, record_id):
    # Delete s3 object
    record = self.get_single(record_id)
    file_path = record.get('data',{}).get('file',{}).get('path','')
    if file_path:
      try:
        FileBehavior().delete(file_path)
      except Exception as e:
        rollbar.report_message(f'Unable to delete file path: {file_path}')

    return super().delete(record_id)
