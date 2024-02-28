from app import db
from ..abstract_asset_type_model import AbstractAssetTypeModel

class EventTypeModel(AbstractAssetTypeModel):
  __tablename__ = 'event_type'
  __table_args = {'extend_existing': True}

  access = db.relationship('EventTypeAccessModel', cascade='all,delete-orphan')

  @classmethod
  def get_asset_model(cls):
    from .event_model import EventModel
    return EventModel