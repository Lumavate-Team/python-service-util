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
from .asset_filetype_rest import AssetFileTypeRestBehavior
from .asset_tag_rest import AssetTagRestBehavior
from ..models import create_asset_category_model
from ..models import create_category_model
from ..models import create_file_asset_model
from ...aws import FileBehavior
from ...name_sort import NameSort
from ...column_select import ColumnSelect
from ...paging import Paging
from ..file_filter import FileFilter

class ContentAssetRestBehavior(AssetRestBehavior):
  def __init__(self, asset_tables, data=None):
    self.asset_tables = asset_tables
    super().__init__(data)

  def get_collection_query(self, asset_table):
    if asset_table is None:
      return None

    q = asset_table.asset_model_class.get_all()

    q = self.apply_filter(q, asset_table.asset_category_model_class)
    q = self.apply_sort(q)
    q = self.apply_select(q, asset_table.asset_category_model_class)
    return q

  def get_collection(self):
    queries = []
    for asset_table in self.asset_tables:
      queries.append(self.get_collection_query(asset_table))

    q = queries.pop(0)

    if len(queries) > 0:
      q = q.union(*queries)

    return Paging().run(q, self.pack)

  def apply_filter(self, q, model_class, ignore_fields=None):
    return FileFilter(self.args, ignore_fields, model_class).apply(q)

  def apply_sort(self, q):
    return NameSort().apply(q)

  def apply_select(self, q, model_class):
    return ColumnSelect(model_class=model_class, args=self.get_args()).apply(q)



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

  def pack(self, rec):
    if rec is None:
      return {}

    return rec.to_json()

    if type(rec) is self._model_class:
      json = rec.to_json()
      if self.expanded('tags') and self.supports_tags():
        json['expand'] = {}
        tags = AssetTagRestBehavior(model_class=self.asset_category_model_class).get_categories_by_asset(rec.id)
        json['expand']['tags'] = [tag.to_json() for tag in tags]

      return json
    else:
      return {self.underscore_to_camel(key):value for(key,value) in rec._asdict().items()}
