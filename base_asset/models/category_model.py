from app import db
from time import time,sleep
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
from hashids import Hashids

from ...db import BaseModel, Column
import json


class CategoryModel(BaseModel):
  __tablename__ = 'category'
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  name = Column(db.String(35), nullable=False)
  type = Column(db.String(35), nullable=False)
  is_active = Column(db.Boolean, server_default=expression.true(), nullable=True)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.is_active==True))

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  @classmethod
  def get_all_by_type(cls, type):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.is_active==True, cls.type==type))

  @classmethod
  def get_by_type(cls, id, type):
    return cls.get_all_by_type(type).filter_by(id=id).first()

  @classmethod
  def get_by_ids(cls, ids):
    return cls.get_all().filter(cls.id.in_(ids))
