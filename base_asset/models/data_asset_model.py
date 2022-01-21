from app import db
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
from lumavate_exceptions import ValidationException, NotFoundException

from .secured_asset_model import SecuredAssetBaseModel
import json


class DataAssetBaseModel(SecuredAssetBaseModel):
  # Add custom columns
  schema_last_modified_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

  @classmethod
  def get_all(cls, args=None):
    return super(SecuredAssetBaseModel, cls).get_all(args)

  @classmethod
  def get(cls, id):
    return super(SecuredAssetBaseModel, cls).get(id)

  @classmethod
  def get_column_definitions(cls, id, include_inactive=False):
    table_asset = cls.get(id)
    if table_asset is None:
      raise NotFoundException(404, 'Invalid Table')
    columns = table_asset.data.get('columns', [])
    if 'columns' not in table_asset.data or table_asset.data['columns'] is None:
      columns = []

    if include_inactive:
      return [c['componentData'] for c in columns]

    return [c['componentData'] for c in columns if c['componentData']['isActive']]

  def to_json(self):
    json = super().to_json()
    json['schema_last_modified_at'] = self.schema_last_modified_at

    return json
