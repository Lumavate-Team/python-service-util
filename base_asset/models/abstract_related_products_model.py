from app import db
from flask import g
from sqlalchemy import or_
from datetime import *
from ...db import BaseModel, Column


class AbstractRelatedProductsModel(BaseModel):
  __abstract__ = True

  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter_by(org_id=g.org_id)
  
  @classmethod
  def set_relations(cls, id, relation_ids):
    cls.delete_relations(id)
    return cls.create_relations(id, relation_ids)
  
  @classmethod
  def get_relations(cls, id):
    return cls.get_all().filter(or_(cls.parent_id==id, cls.child_id==id)).all()

  @classmethod
  def delete_relations(cls, id):
    return cls.get_all().filter(or_(cls.parent_id==id, cls.child_id==id)).delete()

  @classmethod
  def create_relations(cls, primary_id, relation_ids):
    user = g.user['id'] if hasattr(g,'user') and 'id' in g.user else 0
    db.session.bulk_save_objects(
      [
        cls(
          parent_id = primary_id,
          child_id = relation_id,
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