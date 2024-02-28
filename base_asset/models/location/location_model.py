from app import db
from flask import g
from sqlalchemy import ForeignKey, select, and_, cast, Text, case
from sqlalchemy.sql.functions import coalesce
from ....db import Column
from .location_type import LocationTypeModel
from ..abstract_data_asset_model import AbstractDataAssetModel

class LocationModel(AbstractDataAssetModel):
  __tablename__ = 'location'
  __table_args__ = {'extend_existing': True}

  type_id = Column(db.BigInteger, ForeignKey('location_type.id'), nullable=False)

  @classmethod
  def get_type_model(cls):
    return LocationTypeModel
  
  @classmethod
  def get_related_products_model(cls):
    pass
  
  @classmethod
  def get_all_overview(cls, asset_id, args=None):
    asset = cls.get_type_model()
    column_cte = select([
        asset.id,
        cast(asset.data.op('->')('headlineField').op('->>')('columnName'), Text).label('headlineField'), 
        case([(asset.data.op('->')('headlineField').op('->>')('id') == None, True)], else_=False).label('isHeadlineBase'), 
        coalesce(cast(asset.data.op('->')('subheadlineField').op('->>')('columnName'), Text), 'sku').label('subheadlineField'),
        case([(asset.data.op('->')('subheadlineField').op('->>')('id') == None, True)], else_=False).label('isSubheadlineBase')])\
      .select_from(asset)\
      .where(and_(asset.org_id == g.org_id, asset.id == asset_id)) \
      .cte('asset_columns')

    return db.session.query(
        cast(cls.submitted_data.op('->>')('locationName'), Text).label('location_name'),
        case([
          (column_cte.c.isHeadlineBase == True, 
            coalesce(cast(cls.submitted_data.op('->>')(column_cte.c.headlineField), Text),''))],
          else_ = 
            coalesce(cast(cls.submitted_data.op('->')('columns').op('->>')(column_cte.c.headlineField),Text),''))\
        .label('headline_field'),
        case([
          (column_cte.c.subheadlineField == None, 
            None),
          (column_cte.c.isSubheadlineBase == True,
            coalesce(cast(cls.submitted_data.op('->>')(column_cte.c.subheadlineField), Text), None))],
          else_ =
            coalesce(cast(cls.submitted_data.op('->')('columns').op('->>')(column_cte.c.subheadlineField), Text), ''))\
        .label('subheadline_field'),
        cls.public_id,
        cls.type_id
        )\
        .select_from(cls)\
        .join(column_cte, cls.org_id == g.org_id)