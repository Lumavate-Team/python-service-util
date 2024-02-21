from app import db
from sqlalchemy import ForeignKey
from ....db import Column
from .events_related_products import EventsRelatedProductsModel
from .event_type import EventTypeModel
from ..abstract_data_asset_model import AbstractDataAssetModel

class EventModel(AbstractDataAssetModel):
  __tablename__ = 'event'
  __table_args__ = {'extend_existing': True}

  type_id = Column(db.BigInteger, ForeignKey('event_type.id'), nullable=False)

  @classmethod
  def get_type_model(cls):
    return EventTypeModel
  
  @classmethod
  def get_related_products_model(cls):
    return EventsRelatedProductsModel