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


def create_file_asset_model(tablename = 'file_asset'):

  class FileAssetBaseModel(BaseModel):
    __tablename__ = tablename
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
      return cls.query.filter(and_(cls.org_id==g.org_id, cls.is_active==True))

    @classmethod
    def get(cls, id):
      return cls.get_all().filter_by(id=id).first()

    @classmethod
    def get_by_public_id(cls, public_id):
      return cls.get_all().filter_by(public_id=public_id).first()

    def before_insert(self):
      self.set_public_id()
      super().before_insert()

    def set_public_id(self):
      #imports are too fast
      sleep(0.01)
      # get a timestamp to make hash unique since there is no id yet.
      timestamp = int(time() * 1000)
      self.public_id = 'p{}'.format(Hashids(min_length=8,
          salt='T2uDF0uSWF8RwU6IdL0x',
          alphabet='abcdefghijklmnopqrstuvwxyz1234567890').encode(timestamp))

  return FileAssetBaseModel
