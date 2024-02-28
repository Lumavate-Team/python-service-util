from app import db
from sqlalchemy.orm import relationship, backref
from ....db import Column
from ..abstract_related_products_model import AbstractRelatedProductsModel


class ProductsRelatedProductsModel(AbstractRelatedProductsModel):
  __tablename__ = 'products_related_products'

  parent_id = Column(db.String(200), db.ForeignKey('product.public_id'), nullable=False)
  child_id = Column(db.String(200), db.ForeignKey('product.public_id'), nullable=False)

  parent = relationship('ProductModel', backref=backref('products_related_products_parent', cascade='all, delete-orphan'), foreign_keys=parent_id)
  child = relationship('ProductModel', backref=backref('products_related_products_child', cascade='all, delete-orphan'), foreign_keys=child_id)