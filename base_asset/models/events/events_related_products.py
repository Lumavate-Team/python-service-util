from app import db
from sqlalchemy.orm import relationship, backref
from ....db import Column
from ..abstract_related_products_model import AbstractRelatedProductsModel


class EventsRelatedProductsModel(AbstractRelatedProductsModel):
  __tablename__ = 'events_related_products'

  parent_id = Column(db.String(200), db.ForeignKey('event.public_id'), nullable=False)
  child_id = Column(db.String(200), db.ForeignKey('product.public_id'), nullable=False)

  parent = relationship('EventModel', backref=backref('events_related_products_event', cascade='all, delete-orphan'), foreign_keys=parent_id)
  child = relationship('ProductModel', backref=backref('events_related_products_product', cascade='all, delete-orphan'), foreign_keys=child_id)