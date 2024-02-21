from app import db
from flask import g
from sqlalchemy import ForeignKey, select, cast, and_, union, Text, case
from sqlalchemy.sql.functions import coalesce
from ....db import Column
from .events_related_products import EventsRelatedProductsModel
from .event_type import EventTypeModel
from ..abstract_data_asset_model import AbstractDataAssetModel

class EventModel(AbstractDataAssetModel):
  __tablename__ = 'event'
  __table_args__ = {'extend_existing': True}

  type_id = Column(db.BigInteger, ForeignKey('event_type.id'), nullable=False)

  @classmethod
  def get_all_overview(cls, asset_id, args=None):
    asset = EventTypeModel
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
        cast(cls.submitted_data.op('->>')('eventName'), Text).label('event_name'),
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

  @classmethod
  def get_column_definitions(cls, asset_id):
    return EventTypeModel.get_column_definitions(asset_id)

  @classmethod
  def get_related_product_ids(cls, data_id):
    d = cls
    r = EventsRelatedProductsModel

    event_query = select([r.parent_id])\
      .select_from(r)\
      .where(and_(r.child_id == data_id, r.org_id == g.org_id))

    product_query = select([r.child_id])\
      .select_from(r)\
      .where(and_(r.parent_id == data_id, r.org_id == g.org_id))

    return union(event_query, product_query)