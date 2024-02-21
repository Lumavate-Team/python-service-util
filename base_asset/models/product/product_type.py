from app import db
from ..abstract_asset_type_model import AbstractAssetTypeModel

class ProductTypeModel(AbstractAssetTypeModel):
  __tablename__ = 'product_type'
  __table_args = {'extend_existing': True}

  access = db.relationship('ProductTypeAccessModel', cascade='all,delete-orphan')

  @classmethod
  def get_asset_model(cls):
    from .product_model import ProductModel
    return ProductModel