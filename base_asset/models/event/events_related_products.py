from app import db
from flask import g
from sqlalchemy.orm import relationship, backref
from sqlalchemy import or_
from datetime import datetime
from ....db import BaseModel, Column


class EventsRelatedProductsModel(BaseModel):
  __tablename__ = 'events_related_products'
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  event_id = Column(db.String(200), db.ForeignKey('event.public_id'), nullable=False)
  product_id = Column(db.String(200), db.ForeignKey('product.public_id'), nullable=False)

  event = relationship('EventModel', backref=backref('events_related_products_event', cascade='all, delete-orphan'), foreign_keys=event_id)
  product = relationship('ProductModel', backref=backref('events_related_products_product', cascade='all, delete-orphan'), foreign_keys=product_id)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter_by(org_id=g.org_id)

  @classmethod
  def get_relations(cls, id):
    return cls.get_all().filter(or_(cls.event_id==id, cls.product_id==id)).all()

  @classmethod
  def set_relations(cls, id, relation_ids):
    cls.delete_relations(id)
    return cls.create_relations(id, relation_ids)

  @classmethod
  def delete_relations(cls, id):
    return cls.get_all().filter(or_(cls.event_id==id, cls.product_id==id)).delete()

  @classmethod
  def create_relations(cls, primary_id, relation_ids):
    user = g.user['id'] if hasattr(g,'user') else 0
    db.session.bulk_save_objects(
      [
        cls(
          event_id = primary_id,
          product_id = relation_id,
          org_id = g.org_id,
          created_by = user,
          created_at = datetime.utcnow(),
          last_modified_at = datetime.utcnow(),
          last_modified_by = user
        )
        for relation_id in relation_ids
      ])

  @classmethod
  def delete_org(cls, org_id):
    return cls.query.filter_by(org_id=org_id).delete()
