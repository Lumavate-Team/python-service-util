from app import db
from time import time,sleep
from flask import g
from sqlalchemy import and_
from sqlalchemy.sql import expression
from sqlalchemy.dialects.postgresql import JSONB
from hashids import Hashids
from ....db import BaseModel, Column


class ImageAssetModel(BaseModel):
  __tablename__ = 'image_asset'
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