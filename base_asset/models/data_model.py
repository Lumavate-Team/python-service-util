from abc import ABC, ABCMeta, abstractmethod

from app import db
from flask import request, g
from time import time
from sqlalchemy import ForeignKey
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
from lumavate_exceptions import ValidationException
from ...db import BaseModel, Column
from ...enums import ColumnDataType
from ..column import DataColumn
from ..models import AssetBaseModel, DataAssetBaseModel
import json

class DataBaseModel(BaseModel):
  __tablename__='data'
  __table_args__ = {'extend_existing': True}
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False)
  asset_id = Column(db.BigInteger, ForeignKey('asset.id'), nullable=False)
  submitted_data = Column(JSONB, server_default='{}', nullable=True)
  activation_code = Column(db.String(35), nullable=True)
  created_by = Column(db.String(255), nullable=False)
  last_modified_by = Column(db.String(255), nullable=False)
  is_draft = Column(db.Boolean, server_default=expression.false(), nullable=True)
  public_id = Column(db.String(200), nullable=False)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter_by(org_id=g.org_id)

  @classmethod
  def get_all_by_asset_id(cls, asset_id, args=None):
    query = cls.get_all(args).filter_by(asset_id=asset_id)

    if 'draft' in args:
      # python bool cast of a string returns True no matter value if its not empty
      # must compare against string
      draft = args.get('draft') == 'True'
    else:
      draft = True

    exclude_draft = draft == False
    if exclude_draft:
      query = query.filter(or_(cls.is_draft == None,cls.is_draft==False))

    return query

  @classmethod
  def get_all_by_asset_id_activation(cls, asset_id):
    if g.token_data.get('code', None):
      return cls.get_all().filter_by(asset_id=asset_id,activation_code=g.token_data.get('code', None))

    return []

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  @classmethod
  def get_by_public_id(cls, asset_id, public_id):
    return cls.get_all().filter_by(asset_id=asset_id, public_id=public_id).first()

  @validates('asset_id')
  def validate_asset_id(self, key, value):
    if value is not None:
      if AssetBaseModel().get(value) is None:
        raise ValidationException('Invalid asset id', key)
      return value

  @validates('submitted_data')
  def validate_data(self, key, data):
    if not data:
      return data

    if type(data) == str:
      data.replace("'", '"')
      data = json.loads(data)

    schema_columns = self.get_column_definitions(self.asset_id)

    for column_def in schema_columns:
      column = DataColumn.from_json(column_def)
      for data_key, value in data.items():
        if data_key.lower() == column.name.lower():
          if column.column_type == 'text':
            if type(value) != str:
              raise ValidationException('Field must be text', column.dev_name)

          if column.column_type == 'numeric':
            if value in ["", None]:
              continue
            try:
              data[data_key] = float(value)
            except:
              raise ValidationException('Field must be numeric', column.name)

          if column.column_type == 'dropdown':
            pass

          if column.column_type == 'boolean':
            if value not in [True, False, 'true', 'false', 'True', 'False', 'TRUE', 'FALSE', '']:
              raise ValidationException('Field must be valid boolean', column.name)
            if value in ['true', 'True', 'TRUE', True]:
              data[data_key] = True
            elif value in ['false', 'False', False]:
              data[data_key] = False
            else:
              data[data_key] = value

          if column.column_type == 'datetime':
            pass

    return data

  def set_public_id(self):
    pass

  def before_insert(self):
    self.set_public_id()
    super().before_insert()

  def get_column_definitions(self, asset_id):
    return DataAssetBaseModel.get_column_definitions(self.asset_id)

  def to_json(self):
    response = {
      'id': self.public_id,
      'orgId': self.org_id,
      'assetId': self.asset_id,
      'activationCode': self.activation_code,
      'createdBy': self.created_by,
      'createdAt': self.created_at,
      'lastModifiedBy': self.last_modified_by,
      'lastModifiedAt': self.last_modified_at,
      'isDraft': self.is_draft,
      'submittedData': self.submitted_data
    }

    return response
