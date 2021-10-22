from app import db
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
import json
from lumavate_exceptions import ValidationException
from ...db import Column
from .asset_model import AssetBaseModel


class SecuredAssetBaseModel(AssetBaseModel):
  __table_args = {'extend_existing': True}

  access = db.relationship('AssetAccessBaseModel', cascade='all,delete-orphan')
