from app import db
from flask import g
from sqlalchemy import ForeignKey, and_, delete
from ....db import BaseModel, Column
from .video_category_model import VideoCategoryModel

class VideoAssetVideoCategoryModel(BaseModel):
  __tablename__ = 'video_asset_video_category'

  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  asset_id = Column(db.BigInteger, ForeignKey('video_asset.id'), nullable=False)
  category_id = Column(db.BigInteger, ForeignKey('video_category.id'), nullable=False)

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
    return VideoCategoryModel.get_by_ids(cls.query.with_entities(VideoAssetVideoCategoryModel.category_id).filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).all())
  
  @classmethod
  def get_categories_by_type_and_asset(cls, type, asset_id):
    return VideoCategoryModel.get_by_ids_and_type(cls.query.with_entities(VideoAssetVideoCategoryModel.category_id).filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).all(), type)

  @classmethod
  def get_all_by_type_and_asset(cls, type, asset_id):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).\
      join(VideoCategoryModel, VideoCategoryModel.type==type)
  
  @classmethod
  def get_all_by_type_and_ids(cls, type, category_ids):
    return cls.query.filter(and_(cls.org_id==g.org_id)).\
      join(VideoCategoryModel, and_(VideoCategoryModel.id == cls.category_id, VideoCategoryModel.type==type, VideoCategoryModel.id.in_(category_ids)))

  @classmethod
  def delete_all_by_asset(cls, asset_id):
    q = delete(VideoAssetVideoCategoryModel) \
      .where(VideoAssetVideoCategoryModel.org_id == g.org_id) \
      .where(VideoAssetVideoCategoryModel.asset_id == asset_id) 

    return db.session.execute(q)

  @classmethod
  def delete_all_by_type_and_asset(cls, type, asset_id):
    q = delete(VideoAssetVideoCategoryModel) \
      .where(VideoAssetVideoCategoryModel.org_id == g.org_id) \
      .where(VideoAssetVideoCategoryModel.asset_id == asset_id) \
      .where(VideoAssetVideoCategoryModel.category_id == VideoCategoryModel.id) \
      .where(VideoCategoryModel.type == type)

    return db.session.execute(q)