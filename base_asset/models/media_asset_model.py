from app import db
from time import time,sleep
from flask import g
from sqlalchemy import and_
from sqlalchemy.sql import expression
from sqlalchemy.dialects.postgresql import JSONB
from hashids import Hashids
from ...db import BaseModel, Column


class MediaAssetModel(BaseModel):
  __tablename__ = 'media_asset'
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  container_id = Column(db.BigInteger, nullable=False, createable=True, updateable=True, viewable=True)
  old_id = Column(db.BigInteger, nullable=False, createable=True, updateable=True, viewable=True)
  asset_type = Column(db.String(35), nullable=False)
  public_id = Column(db.String(200), nullable=False)
  name = Column(db.String(35), nullable=False)
  filename = Column(db.String(250))
  image = Column(JSONB, default=lambda: {}, nullable=True)
  data = Column(JSONB)
  dependency_assets = Column(JSONB)
  is_active = Column(db.Boolean, server_default=expression.true(), nullable=True)
  created_by = Column(db.String(250), nullable=False)
  last_modified_by = Column(db.String(250), nullable=False)

  @classmethod
  def get_all(cls):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.is_active==True))
  
  @classmethod
  def get_all_current_container(cls):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.container_id==cls._get_current_container(), cls.is_active==True))

  @classmethod
  def get(cls, old_id):
    return cls.get_all().filter_by(old_id=old_id).first()

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
