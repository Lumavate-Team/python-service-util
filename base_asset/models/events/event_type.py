from app import db
from flask import g
from sqlalchemy import and_, func
from ..abstract_asset_type_model import AbstractAssetTypeModel
from events import EventModel

class EventTypeModel(AbstractAssetTypeModel):
  __tablename__ = 'event_type'
  __table_args = {'extend_existing': True}

  access = db.relationship('EventTypeAccessModel', cascade='all,delete-orphan')

  @classmethod
  def get_all_with_counts(cls, args=None):
    counts  = db.session.query(
      cls.id.label('event_type_id'), 
      func.count(EventModel.id).label('data_count')
    )\
    .outerjoin(EventModel, and_(cls.id == EventModel.event_type_id, cls.org_id == g.org_id))\
    .group_by(cls.id)\
    .subquery()

    data_counts = db.session.query(
        cls,
        counts.c.data_count.label('data_count'),
    )\
    .select_from(cls)\
    .join(counts, counts.c.event_type_id == cls.id)\
    .filter(cls.org_id == g.org_id)

    return data_counts