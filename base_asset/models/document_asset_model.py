from app import db
from time import time,sleep
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
from hashids import Hashids
from lumavate_exceptions import ValidationException, NotFoundException

from .file_asset_model import FileAssetBaseModel


class DocumentAssetModel(FileAssetBaseModel):
  __tablename__ = 'document_asset'
