from app import db
from flask import g
from sqlalchemy import ForeignKey
from ....db import Column
from ..abstract_asset_type_access_model import AbstractAssetTypeAccessModel


class EventTypeAccessModel(AbstractAssetTypeAccessModel):
  __tablename__ = 'event_type_access'
  __table_args = {'extend_existing': True}

  type_id = Column(db.BigInteger, ForeignKey('event_type.id'), nullable=False)