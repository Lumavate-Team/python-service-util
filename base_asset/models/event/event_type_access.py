from app import db
from flask import g
from sqlalchemy import ForeignKey
from ....db import Column
from ..abstract_asset_type_access_model import AbstractAssetTypeAccessModel


class EventTypeAccessModel(AbstractAssetTypeAccessModel):
  __tablename__ = 'event_type_access'
  __table_args = {'extend_existing': True}

  event_type_id = Column(db.BigInteger, ForeignKey('event_type.id'), nullable=False)

  @classmethod
  def get_by_asset(cls, asset_id, return_default=True):
    access_rec = cls.get_all().filter_by(event_type_id=asset_id).first()

    if access_rec is None and return_default:
      access_rec = EventTypeAccessModel(
          org_id=g.org_id,
          event_type_id=asset_id,
          get_access = 'none',
          post_access= 'all',
          put_access = 'none',
          delete_access = 'none')

    return access_rec