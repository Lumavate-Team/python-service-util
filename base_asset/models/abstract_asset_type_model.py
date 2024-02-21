from app import db
from flask import g
from sqlalchemy import and_, func, select
from sqlalchemy.sql import expression
from sqlalchemy.dialects.postgresql import JSONB
from lumavate_exceptions import NotFoundException
from ...db import BaseModel, Column
from ...enums import ColumnDataType

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
  
  #TODO: Consolidate with table builder into service util base data asset model
  @classmethod
  def get_file_column_names(cls, asset_id):
    data_column = func.jsonb_array_elements(cls.data.op('->')('columns'))

    data_columns_cte = \
      select([
        data_column.label('data_column')])\
      .select_from(cls)\
      .where(and_(cls.id == asset_id, cls.org_id == g.org_id))\
      .cte('data_columns')

    file_column_query = \
      select([data_columns_cte.c.data_column.op('->')('componentData').op('->>')('columnName')])\
      .select_from(data_columns_cte)\
      .where(data_columns_cte.c.data_column.op('->')('componentData').op('->')('columnType').op('->>')('value') == ColumnDataType.FILE)
    file_columns = db.session.execute(file_column_query)

    return [f[0] for f in file_columns]
  
  @classmethod
  def delete_org(cls, org_id):
    return cls.query.filter_by(org_id=org_id).delete()
