from app import db
from flask import g
from sqlalchemy import ForeignKey, and_, delete
from ....db import BaseModel, Column
from .document_category_model import DocumentCategoryModel

class DocumentAssetDocumentCategoryModel(BaseModel):
  __tablename__ = 'document_asset_document_category'

  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  asset_id = Column(db.BigInteger, ForeignKey('document_asset.id'), nullable=False)
  category_id = Column(db.BigInteger, ForeignKey('document_category.id'), nullable=False)

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
    return DocumentCategoryModel.get_by_ids(cls.query.with_entities(DocumentAssetDocumentCategoryModel.category_id).filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).all())
  
  @classmethod
  def get_categories_by_type_and_asset(cls, type, asset_id):
    return DocumentCategoryModel.get_by_ids_and_type(cls.query.with_entities(DocumentAssetDocumentCategoryModel.category_id).filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).all(), type)

  @classmethod
  def get_categories_by_assets(cls, asset_ids):
    return DocumentCategoryModel.get_by_ids(cls.query.with_entities(DocumentAssetDocumentCategoryModel.category_id).filter(and_(cls.org_id==g.org_id, cls.asset_id.in_(asset_ids))).all())
  
  @classmethod
  def get_categories_by_type_and_assets(cls, type, asset_ids):
    return cls.query.with_entities(DocumentCategoryModel, DocumentAssetDocumentCategoryModel).filter(and_(cls.org_id==g.org_id, cls.asset_id.in_(asset_ids))).\
      join(DocumentCategoryModel, and_(DocumentCategoryModel.id == cls.category_id, DocumentCategoryModel.type==type))
  
  @classmethod
  def get_all_by_type_and_asset(cls, type, asset_id):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.asset_id==asset_id)).\
      join(DocumentCategoryModel, DocumentCategoryModel.type==type)
  
  @classmethod
  def get_all_by_type_and_ids(cls, type, category_ids):
    return cls.query.filter(and_(cls.org_id==g.org_id)).\
      join(DocumentCategoryModel, and_(DocumentCategoryModel.id == cls.category_id, DocumentCategoryModel.type==type, DocumentCategoryModel.id.in_(category_ids)))

  @classmethod
  def get_all_by_ids(cls, category_ids):
    return cls.query.filter(and_(cls.org_id==g.org_id)).\
      join(DocumentCategoryModel, and_(DocumentCategoryModel.id == cls.category_id, DocumentCategoryModel.id.in_(category_ids)))

  @classmethod
  def delete_all_by_asset(cls, asset_id):
    q = delete(DocumentAssetDocumentCategoryModel) \
      .where(DocumentAssetDocumentCategoryModel.org_id == g.org_id) \
      .where(DocumentAssetDocumentCategoryModel.asset_id == asset_id) 

    return db.session.execute(q)

  @classmethod
  def delete_all_by_type_and_asset(cls, type, asset_id):
    q = delete(DocumentAssetDocumentCategoryModel) \
      .where(DocumentAssetDocumentCategoryModel.org_id == g.org_id) \
      .where(DocumentAssetDocumentCategoryModel.asset_id == asset_id) \
      .where(DocumentAssetDocumentCategoryModel.category_id == DocumentCategoryModel.id) \
      .where(DocumentCategoryModel.type == type)

    return db.session.execute(q)

  @classmethod
  def delete_org(cls, org_id):
    return cls.query.filter_by(org_id=org_id).delete()