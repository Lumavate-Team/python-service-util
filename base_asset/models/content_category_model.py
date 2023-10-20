from app import db
from flask import g
from sqlalchemy import and_, or_, desc
from sqlalchemy.sql import expression
from ...db import BaseModel, Column


class ContentCategoryModel(BaseModel):
  __tablename__ = 'content_category'
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  container_id = Column(db.BigInteger, nullable=False, createable=True, updateable=True, viewable=True)
  old_id = Column(db.BigInteger, nullable=False, createable=True, updateable=True, viewable=True)
  name = Column(db.String(35), nullable=False)
  type = Column(db.String(35), nullable=False)
  is_active = Column(db.Boolean, server_default=expression.true(), nullable=True)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter(and_(or_(cls.org_id==g.org_id, cls.org_id==None), cls.is_active==True, cls.container_id==cls._get_current_container()))

  @classmethod
  def get(cls, old_id):
    return cls.get_all().filter_by(old_id=old_id).first()

  @classmethod
  def get_all_by_type(cls, type):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.container_id==cls._get_current_container(), cls.is_active==True, cls.type==type))

  @classmethod
  def get_by_type(cls, old_id, type):
    return cls.get_all_by_type(type).filter_by(old_id=old_id).first()

  @classmethod
  def get_by_ids(cls, old_ids):
    return cls.get_all().filter(cls.old_id.in_(old_ids))

  @classmethod
  def get_by_ids_and_type(cls, old_ids, type):
    return cls.get_all().filter(and_(cls.old_id.in_(old_ids), cls.type==type))

  @classmethod
  def get_by_name_and_type(cls, name, type):
    return cls.get_all().filter_by(name=name, type=type).first()
  
  @classmethod
  def get_by_primary_ids(cls, ids):
    return cls.get_all().filter(cls.id.in_(ids))

  @classmethod
  def get_by_primary_ids_and_type(cls, ids, type):
    return cls.get_all().filter(and_(cls.id.in_(ids), cls.type==type))