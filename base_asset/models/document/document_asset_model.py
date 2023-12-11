from ..abstract_asset_model import AbstractAssetBaseModel
from app import db
from time import time,sleep
from flask import g
from sqlalchemy import and_, literal_column
from sqlalchemy.sql import expression
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import column_property
from hashids import Hashids
from ....db import Column

class DocumentAssetModel(AbstractAssetBaseModel):
  __tablename__ = 'document_asset'