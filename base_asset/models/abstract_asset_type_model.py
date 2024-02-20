from app import db
from flask import g
from sqlalchemy import and_
from sqlalchemy.sql import expression
from sqlalchemy.dialects.postgresql import JSONB
from lumavate_exceptions import NotFoundException
from ...db import BaseModel, Column

class AbstractAssetTypeModel(BaseModel):
  __abstract__ = True

  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  name = Column(db.String(35), nullable=False)
  image = Column(JSONB, default=lambda: {}, nullable=True)
  is_active = Column(db.Boolean, server_default=expression.true(), nullable=True)
  data = Column(JSONB)
  dependency_assets = Column(JSONB)

  created_by = Column(db.String(250), nullable=False)
  last_modified_by = Column(db.String(250), nullable=False)
  schema_last_modified_at = Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.is_active==True))

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

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
  
  @classmethod
  def delete_org(cls, org_id):
    return cls.query.filter_by(org_id=org_id).delete()
