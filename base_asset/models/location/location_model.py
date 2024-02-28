from app import db
from sqlalchemy import ForeignKey
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