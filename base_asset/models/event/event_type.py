from app import db
from flask import g
from sqlalchemy import and_, func, select
from ....enums import ColumnDataType
from ..abstract_asset_type_model import AbstractAssetTypeModel
from ...models import EventModel

class EventTypeModel(AbstractAssetTypeModel):
  __tablename__ = 'event_type'
  __table_args = {'extend_existing': True}

  access = db.relationship('EventTypeAccessModel', cascade='all,delete-orphan')

  @classmethod
  def get_all_with_counts(cls, args=None):
    a = EventTypeModel
    d = EventModel

    counts  = db.session.query(
      a.id.label('event_type_id'), 
      func.count(d.id).label('data_count')
    )\
    .outerjoin(d, and_(a.id == d.event_type_id, a.org_id == g.org_id))\
    .group_by(a.id)\
    .subquery()

    data_counts = db.session.query(
        EventTypeModel,
        counts.c.data_count.label('data_count'),
    )\
    .select_from(EventTypeModel)\
    .join(counts, counts.c.event_type_id == a.id)\
    .filter(a.org_id == g.org_id)

    return data_counts

  #TODO: Consolidate with table builder into service util base data asset model
  @classmethod
  def get_file_column_names(cls, asset_id):
    data_column = func.jsonb_array_elements(EventTypeModel.data.op('->')('columns'))

    data_columns_cte = \
      select([
        data_column.label('data_column')])\
      .select_from(EventTypeModel)\
      .where(and_(EventTypeModel.id == asset_id, EventTypeModel.org_id == g.org_id))\
      .cte('data_columns')

    file_column_query = \
      select([data_columns_cte.c.data_column.op('->')('componentData').op('->>')('columnName')])\
      .select_from(data_columns_cte)\
      .where(data_columns_cte.c.data_column.op('->')('componentData').op('->')('columnType').op('->>')('value') == ColumnDataType.FILE)
    file_columns = db.session.execute(file_column_query)

    return [f[0] for f in file_columns]