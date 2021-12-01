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


class FileAssetBaseModel(AssetBaseModel):
  __tablename__ = 'asset'
  __table_args__ = {'extend_existing': True}
  # Add custom columns
  filename = Column(db.String(250))

  @classmethod
  def get_all(cls, args=None):
    return super(FileAssetBaseModel, cls).get_all(args)

  @classmethod
  def get(cls, id):
    return super(FileAssetBaseModel, cls).get(id)
