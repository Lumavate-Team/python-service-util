from app import db
from sqlalchemy import ForeignKey
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