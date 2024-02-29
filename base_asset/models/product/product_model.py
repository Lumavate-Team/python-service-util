from app import db
from flask import g
from sqlalchemy import ForeignKey, cast, Text
from ....db import Column
from .products_related_products import ProductsRelatedProductsModel
from .product_type import ProductTypeModel
from ..abstract_data_asset_model import AbstractDataAssetModel

class ProductModel(AbstractDataAssetModel):
  __tablename__ = 'product'
  __table_args__ = {'extend_existing': True}

  type_id = Column(db.BigInteger, ForeignKey('product_type.id'), nullable=False)

  @classmethod
  def get_type_model(cls):
    return ProductTypeModel
  
  @classmethod
  def get_related_products_model(cls):
    return ProductsRelatedProductsModel
  
  @classmethod
  def cast_data_name_column(cls):
    return cast(cls.submitted_data.op('->>')('productName'), Text).label('product_name')