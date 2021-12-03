from app import db
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
from lumavate_exceptions import ValidationException, NotFoundException

from ...db import BaseModel, Column
from .asset_model import AssetBaseModel
import json


class FileAssetBaseModel(BaseModel):
  __tablename__ = 'file_asset'
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  name = Column(db.String(35), nullable=False)
  image = Column(JSONB, default=lambda: {}, nullable=True)
  is_active = Column(db.Boolean, server_default=expression.true(), nullable=True)
  data = Column(JSONB)
  dependency_assets = Column(JSONB)
  filename = Column(db.String(250))

  created_by = Column(db.String(250), nullable=False)
  last_modified_by = Column(db.String(250), nullable=False)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.is_active==True))

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()
