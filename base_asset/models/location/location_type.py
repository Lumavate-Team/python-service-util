from app import db
from ..abstract_asset_type_model import AbstractAssetTypeModel

class LocationTypeModel(AbstractAssetTypeModel):
  __tablename__ = 'location_type'
  __table_args = {'extend_existing': True}

  access = db.relationship('LocationTypeAccessModel', cascade='all,delete-orphan')

  @classmethod
  def get_asset_model(cls):
    from .location_model import LocationModel
    return LocationModel
  
  @classmethod
  def get_all_with_counts(cls, args=None):
    pass

  @classmethod
  def get_column_definitions(cls, id, include_inactive=False):
    pass