from app import db
from time import time,sleep
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from hashids import Hashids
from lumavate_exceptions import ValidationException, NotFoundException

from ...db import BaseModel, Column
from .asset_model import AssetBaseModel
import json


def create_content_asset_model(asset_types):
  DynamicBase = declarative_base(cls=BaseModel, class_registry=dict())

  class ContentAssetBaseModel(DynamicBase):
    __tablename__ = asset_types[0].file_model
    __table_args__ = {'extend_existing': True}
    org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
    name = Column(db.String(35), nullable=False)
    image = Column(JSONB, default=lambda: {}, nullable=True)
    is_active = Column(db.Boolean, server_default=expression.true(), nullable=True)
    data = Column(JSONB)
    dependency_assets = Column(JSONB)
    filename = Column(db.String(250))
    public_id = Column(db.String(200), nullable=False)

    created_by = Column(db.String(250), nullable=False)
    last_modified_by = Column(db.String(250), nullable=False)

    @classmethod
    def get_all(cls, args=None):
      q = cls.query.filter(and_(cls.org_id==g.org_id, cls.is_active==True))

      return q

    @classmethod
    def get(cls, id):
      return cls.get_all().filter_by(id=id).first()

    @classmethod
    def get_by_public_id(cls, public_id):
      return cls.get_all().filter_by(public_id=public_id).first()

  return FileAssetBaseModel
