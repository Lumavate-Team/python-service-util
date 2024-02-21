from app import db
from flask import g
from ...db import BaseModel, Column


class AbstractAssetTypeAccessModel(BaseModel):
  __abstract__ = True

  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
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
  def get_by_asset(cls, asset_id, return_default=True):
    access_rec = cls.get_all().filter_by(type_id=asset_id).first()

    if access_rec is None and return_default:
      access_rec = cls(
          org_id=g.org_id,
          type_id=asset_id,
          get_access = 'none',
          post_access= 'all',
          put_access = 'none',
          delete_access = 'none')

    return access_rec
  
  @classmethod
  def delete_org(cls, org_id):
    return cls.query.filter_by(org_id=org_id).delete()