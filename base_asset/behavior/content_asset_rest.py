from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from lumavate_properties import Properties, Components
from lumavate_exceptions import ValidationException, NotFoundException, ApiException
from sqlalchemy import or_, cast, VARCHAR, func, union_all
import itertools
import rollbar
from app import db
import os
import re
import json
from .asset_rest import AssetRestBehavior
from .asset_filetype_rest import AssetFileTypeRestBehavior
from .asset_tag_rest import AssetTagRestBehavior
from ...aws import FileBehavior
from ...name_sort import NameSort
from ..content_column_select import ContentColumnSelect
from ..content_paging import ContentPaging
from ..content_filter import ContentFilter
from ..models import AbstractAssetBaseModel
from sqlalchemy.orm import class_mapper
from sqlalchemy import literal_column
from ..models.document.document_asset_model import DocumentAssetModel
from ..models.image.image_asset_model import ImageAssetModel
from ..models.audio.audio_asset_audio_category_model import AudioAssetAudioCategoryModel

class ContentAssetRestBehavior(AssetRestBehavior):
  def __init__(self, asset_tables, data=None):
    self.asset_tables = asset_tables
    super().__init__(data)

  def should_query(self, asset_type):
    asset_types = ['audio', 'document', 'image', 'video']
    user_filters_set = False
    hidden_filters_set = False

    if self.get_args() is None:
      return True

    for arg in self.get_args():
      for iterate_asset_type in asset_types:
        if arg.startswith(iterate_asset_type + '_'):
          user_filters_set = True
        if arg.startswith('hf_' + iterate_asset_type + '_'):
          hidden_filters_set = True

    if not user_filters_set and not hidden_filters_set:
      return True

    if user_filters_set and hidden_filters_set:
      if any(key.startswith(asset_type + '_') for key in self.get_args()) and any(key.startswith('hf_' + asset_type + '_') for key in self.get_args()):
        return True
    elif user_filters_set:
      if any(key.startswith(asset_type + '_') for key in self.get_args()):
        return True
    elif hidden_filters_set:
      if any(key.startswith('hf_' + asset_type + '_') for key in self.get_args()):
        return True

    return False

  def get_collection_query(self, asset_table):
    if asset_table is None:
      return None

    q = asset_table.asset_model_class.get_all()

    q = self.apply_filter(q, asset_table.asset_category_model_class, ['org_id'], asset_table.asset_type)
    q = self.apply_sort(q)
    q = self.apply_select(q, asset_table.asset_model_class, asset_table.asset_type)
    return q

  def get_collection(self):
    queries = []
    for asset_table in self.asset_tables:
      if self.should_query(asset_table.asset_type):
        queries.append(self.get_collection_query(asset_table))

    q = queries.pop(0)

    if len(queries) > 0:
      q = q.union(*queries)

    return ContentPaging().run(q, self.pack)

  def apply_filter(self, q, model_class, ignore_fields=None, asset_type=None):
    return ContentFilter(self.args, ignore_fields, model_class, asset_type).apply(q)

  def apply_sort(self, q):
    return NameSort().apply(q)

  def apply_select(self, q, model_class, asset_type):
    return ContentColumnSelect(model_class=model_class, asset_type=asset_type, args=self.get_args()).apply(q)
  
  def pack(self, rec):
    if rec is None:
      return {}
    
    if self.expanded('tags') and self.supports_tags():
      record = dict(rec)
      record['expand'] = {}

      assetTable = next(asset_table for asset_table in self.asset_tables if asset_table.asset_type == (record['asset_type'] if ('asset_type' in record) else record['anon_1_asset_type']))

      tags = AssetTagRestBehavior(model_class=assetTable.asset_category_model_class).get_categories_by_asset(record['id'])
      record['expand']['tags'] = [(dict(tag.to_json())) for tag in tags]

    return record

  def supports_filetype_category(self):
    return False

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

  def get_asset_properties(self):
    raise ApiException(500, "get asset properties not implemented")
