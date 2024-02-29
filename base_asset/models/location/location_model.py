from app import db
from flask import g
from sqlalchemy import ForeignKey, cast, Text
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
  def cast_data_name_column(cls):
    return cast(cls.submitted_data.op('->>')('locationName'), Text).label('location_name')