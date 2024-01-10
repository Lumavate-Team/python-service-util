from app import db
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
import json
from lumavate_exceptions import ValidationException
from ...db import BaseModel, Column


class AssetAccessBaseModel(BaseModel):
  __tablename__ = 'asset_access'
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  asset_id = Column(db.BigInteger, ForeignKey('asset.id'), nullable=False)
  get_access = Column(db.String(30), nullable=False, default='none')
  post_access = Column(db.String(30), nullable=False, default='all')
  put_access = Column(db.String(30), nullable=False, default='none')
  delete_access = Column(db.String(30), nullable=False, default='none')

  created_by = db.Column(db.String(250), nullable=False)
  last_modified_by = db.Column(db.String(250), nullable=False)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter(cls.org_id==g.org_id)

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  @classmethod
  def delete_org(cls, org_id):
    return cls.query.filter_by(org_id=org_id).delete()

  @classmethod
  def get_by_asset(cls, asset_id, return_default=True):
    access_rec = cls.get_all().filter_by(asset_id=asset_id).first()

    if access_rec is None and return_default:
      access_rec = AssetAccessBaseModel(
          org_id=g.org_id,
          asset_id=asset_id,
          get_access = 'none',
          post_access= 'all',
          put_access = 'none',
          delete_access = 'none')

    return access_rec

