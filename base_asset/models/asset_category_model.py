from app import db
from time import time,sleep
from flask import request, g
from sqlalchemy import ForeignKey, and_, delete
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
from hashids import Hashids

from ...db import BaseModel, Column
from .category_model import create_category_model
import json

def create_asset_category_model(tablename = 'asset_category', category_model = create_category_model()):
  class AssetCategoryModel(BaseModel):
    __tablename__ = tablename
    __table_args__ = {'extend_existing': True}
    org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
    asset_id = Column(db.BigInteger, ForeignKey('asset.id'), nullable=False)
    category_id = Column(db.BigInteger, ForeignKey('category.id'), nullable=False)

    @classmethod
    def get(cls, id):
      return cls.get_all().filter_by(id=id).first()

    @classmethod
    def get_all(cls, args=None):
      return cls.query.filter(cls.org_id==g.org_id)

    @classmethod
    def get_all_by_asset(cls, asset_id):
      return cls.query.filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id))

    @classmethod
    def get_categories_by_asset(cls, asset_id):
      return category_model.get_by_ids(cls.query.with_entities(AssetCategoryModel.category_id).filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).all())
    
    @classmethod
    def get_categories_by_type_and_asset(cls, type, asset_id):
      return category_model.get_by_ids_and_type(cls.query.with_entities(AssetCategoryModel.category_id).filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).all(), type)

    @classmethod
    def get_all_by_type_and_asset(cls, type, asset_id):
      return cls.query.filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).\
        join(category_model, category_model.type==type)
    
    @classmethod
    def get_all_by_type_and_ids(cls, type, category_ids):
      return cls.query.filter(and_(cls.org_id==g.org_id)).\
        join(category_model, and_(category_model.id == cls.category_id, category_model.type==type, category_model.id.in_(category_ids)))

    @classmethod
    def delete_all_by_asset(cls, asset_id):
      q = delete(AssetCategoryModel) \
        .where(AssetCategoryModel.org_id == g.org_id) \
        .where(AssetCategoryModel.asset_id == asset_id) 

      return db.session.execute(q)

    @classmethod
    def delete_all_by_type_and_asset(cls, type, asset_id):
      q = delete(AssetCategoryModel) \
        .where(AssetCategoryModel.org_id == g.org_id) \
        .where(AssetCategoryModel.asset_id == asset_id) \
        .where(AssetCategoryModel.category_id == category_model.id) \
        .where(category_model.type == type)

      return db.session.execute(q)

  return AssetCategoryModel