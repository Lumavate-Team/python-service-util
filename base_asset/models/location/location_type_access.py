from app import db
from sqlalchemy import ForeignKey
from ....db import Column
from ..abstract_asset_type_access_model import AbstractAssetTypeAccessModel


class LocationTypeAccessModel(AbstractAssetTypeAccessModel):
  __tablename__ = 'location_type_access'
  __table_args = {'extend_existing': True}

  type_id = Column(db.BigInteger, ForeignKey('location_type.id'), nullable=False)