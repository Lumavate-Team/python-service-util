from app import db
from flask import request, g
from sqlalchemy import ForeignKey, and_
from sqlalchemy.sql import text, expression
from sqlalchemy.orm import validates, relationship, load_only
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.dialects.postgresql import JSONB
import json
from lumavate_exceptions import ValidationException
from .db import BaseModel, Column


class AssetBaseModel(BaseModel):
  __tablename__ = 'asset'
  id = db.Column(db.BigInteger, primary_key=True)
  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  name = Column(db.String(35), nullable=False)
  image = Column(JSONB, default=lambda: {}, nullable=True)
  is_active = Column(db.Boolean, server_default=expression.true(), nullable=True)
  data = Column(JSONB)

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter(and_(cls.org_id==g.org_id, cls.is_active==True))

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()

  def to_json(self):
    json_payload = super().to_json()

    return json_payload

