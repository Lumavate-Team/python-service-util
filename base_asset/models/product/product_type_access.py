from app import db
from flask import g
from sqlalchemy import ForeignKey
from ....db import Column
from ..abstract_asset_type_access_model import AbstractAssetTypeAccessModel


class ProductTypeAccessModel(AbstractAssetTypeAccessModel):
  __tablename__ = 'product_type_access'
  __table_args = {'extend_existing': True}

  type_id = Column(db.BigInteger, ForeignKey('product_type.id'), nullable=False)