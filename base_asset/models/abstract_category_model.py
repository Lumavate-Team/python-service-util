from app import db
from flask import g
from sqlalchemy import and_
from sqlalchemy.sql import expression
from sqlalchemy import or_
from ...db import BaseModel, Column

class AbstractCategoryModel(BaseModel):
    __abstract__ = True

    org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
    name = Column(db.String(35), nullable=False)
    type = Column(db.String(35), nullable=False)
    is_active = Column(db.Boolean, server_default=expression.true(), nullable=True)

    @classmethod
    def get_all(cls, args=None):
      return cls.query.filter(and_(or_(cls.org_id==g.org_id, cls.org_id==None), cls.is_active==True))

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

    @classmethod
    def get_by_ids_and_type(cls, ids, type):
      return cls.get_all().filter(and_(cls.id.in_(ids), cls.type==type))

    @classmethod
    def get_by_name_and_type(cls, name, type):
      return cls.get_all().filter_by(name=name, type=type).first()

    @classmethod
    def delete_org(cls, org_id):
      return cls.query.filter_by(org_id=org_id).delete()