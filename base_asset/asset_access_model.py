from app import db
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
import json
from lumavate_exceptions import ValidationException
from .db import BaseModel, Column


class AssetAccessBaseModel(BaseModel):
  __tablename__ = 'asset_access'
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  asset_id = Column(db.BigInteger, ForeignKey('asset.id'), nullable=False)
  request_method = Column(db.String(10), nullable=False)
  access_level = Column(db.String(30), nullable=False)

  created_by = db.Column(db.String(250), nullable=False)
  last_modified_by = db.Column(db.String(250), nullable=False)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter(cls.org_id==g.org_id)

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  @classmethod
  def get_by_asset(cls, asset_id):
    return cls.get_all().filter_by(cls.asset_id=asset_id)

  @classmethod
  def get_by_request_method(cls, asset_id, method):
    return cls.get_all().filter(and_(cls.asset_id=asset_id, cls.request_method=method))

