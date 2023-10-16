from app import db
from flask import g
from sqlalchemy import ForeignKey, and_, delete
from ...db import BaseModel, Column
from .content_category_model import ContentCategoryModel


class ContentCategoryMediaAssetModel(BaseModel):
  __tablename__ = 'content_category_media_asset'
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  media_asset_id = Column(db.BigInteger, ForeignKey('media_asset.id'), nullable=False)
  content_category_id = Column(db.BigInteger, ForeignKey('content_category.id'), nullable=False)

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter(cls.org_id==g.org_id)

  @classmethod
  def get_all_by_asset(cls, media_asset_id):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.media_asset_id==media_asset_id))

  @classmethod
  def get_categories_by_asset(cls, media_asset_id):
    return ContentCategoryModel.get_by_ids(cls.query.with_entities(ContentCategoryMediaAssetModel.content_category_id).filter(and_(cls.org_id==g.org_id, cls.media_asset_id==media_asset_id)).all())
  
  @classmethod
  def get_categories_by_type_and_asset(cls, type, media_asset_id):
    return ContentCategoryModel.get_by_ids_and_type(cls.query.with_entities(ContentCategoryMediaAssetModel.content_category_id).filter(and_(cls.org_id==g.org_id, cls.media_asset_id==media_asset_id)).all(), type)

  @classmethod
  def get_all_by_type_and_asset(cls, type, media_asset_id):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.media_asset_id==media_asset_id)).\
      join(ContentCategoryModel, ContentCategoryModel.type==type)
  
  @classmethod
  def get_all_by_type_and_ids(cls, type, category_ids):
    return cls.query.filter(and_(cls.org_id==g.org_id)).\
      join(ContentCategoryModel, and_(ContentCategoryModel.id == cls.content_category_id, ContentCategoryModel.type==type, ContentCategoryModel.id.in_(category_ids)))

  @classmethod
  def delete_all_by_asset(cls, media_asset_id):
    q = delete(ContentCategoryMediaAssetModel) \
      .where(ContentCategoryMediaAssetModel.org_id == g.org_id) \
      .where(ContentCategoryMediaAssetModel.media_asset_id == media_asset_id) 

    return db.session.execute(q)

  @classmethod
  def delete_all_by_type_and_asset(cls, type, media_asset_id):
    q = delete(ContentCategoryMediaAssetModel) \
      .where(ContentCategoryMediaAssetModel.org_id == g.org_id) \
      .where(ContentCategoryMediaAssetModel.media_asset_id == media_asset_id) \
      .where(ContentCategoryMediaAssetModel.content_category_id == ContentCategoryModel.id) \
      .where(ContentCategoryModel.type == type)

    return db.session.execute(q)