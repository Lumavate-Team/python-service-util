from sqlalchemy.orm.interfaces import MapperExtension
from datetime import datetime, date
import sqlalchemy
from sqlalchemy import desc
from sqlalchemy.schema import Sequence
from sqlalchemy.inspection import inspect
from sqlalchemy_utils.functions import get_query_entities
from sqlalchemy.engine.url import make_url
from flask import g, current_app, request
from sqlalchemy.inspection import inspect
from flask_sqlalchemy import (SQLAlchemy, BaseQuery, SignallingSession,
        SessionBase, _record_queries, _EngineDebuggingSignalEvents)
from itsdangerous import URLSafeSerializer
from itertools import chain
import requests
import json
import os
import re
from .util import camel_to_underscore, underscore_to_camel

from lumavate_exceptions import ValidationException
import lumavate_service_util as util
try:
  from app import db
except:
  db = None

# Base Validator
class Validator(MapperExtension):
  def after_insert(self, mapper, connection, instance):
    if hasattr(instance, 'after_insert') and callable(getattr(instance, 'after_insert')):
      instance.after_insert()

    if hasattr(instance, 'after_change') and callable(getattr(instance, 'after_change')):
      instance.after_change()

  def after_update(self, mapper, connection, instance):
    if hasattr(instance, 'after_update') and callable(getattr(instance, 'after_update')):
      instance.after_update()

    if hasattr(instance, 'after_change') and callable(getattr(instance, 'after_change')):
      instance.after_change()

  def after_delete(self, mapper, connection, instance):
    if hasattr(instance, 'after_delete') and callable(getattr(instance, 'after_delete')):
      instance.after_delete()

def add_pre_commit_hook(h):
  if not hasattr(g, 'on_pre_commit_hooks'):
    g.on_pre_commit_hooks = []

  g.on_pre_commit_hooks.append(h)

def add_post_commit_hook(h):
  if not hasattr(g, 'on_post_commit_hooks'):
    g.on_post_commit_hooks = []

  g.on_post_commit_hooks.append(h)

@sqlalchemy.event.listens_for(db.session.__class__, 'after_begin')
def before_begin(session, a, b):
  g.in_transaction = True

@sqlalchemy.event.listens_for(db.session.__class__, 'before_commit')
def receive_before_commit(session):
  if hasattr(g, 'on_pre_commit_hooks'):
    for h in g.on_pre_commit_hooks:
      h()

    g.on_pre_commit_hooks = []

@sqlalchemy.event.listens_for(db.session.__class__, 'after_rollback')
def receive_after_rollback(session):
  g.in_transaction = False

@sqlalchemy.event.listens_for(db.session.__class__, 'after_commit')
def receive_after_commit(session):
  g.in_transaction = False
  if hasattr(g, 'on_post_commit_hooks'):
    while len(g.on_post_commit_hooks) > 0:
      h = g.on_post_commit_hooks.pop(0)
      h()

@sqlalchemy.event.listens_for(db.session.__class__, 'before_flush')
def receive_before_flush(session, flush_context, instances):
  for i in session.new:
    if hasattr(i, 'before_insert'):
      i.before_insert()

    if hasattr(i, 'validate'):
      i.validate()

  for i in session.dirty:
    if hasattr(i, 'before_update'):
      i.before_update()

    if hasattr(i, 'validate'):
      i.validate()

  for i in session.deleted:
    if hasattr(i, 'before_delete'):
      i.before_delete()

    if hasattr(i, 'validate_delete'):
      i.validate_delete()

class Column(db.Column):
  def __init__(self, *args, **kwargs):
    # Able to be used to describe objects
    self.discoverable = kwargs.pop('discoverable', True)
    # Able to be used to create objects
    self.createable = kwargs.pop('createable', True)
    # Able to be used to update objects
    self.updateable = kwargs.pop('updateable', True)
    # Able to be used to get objects
    self.viewable = kwargs.pop('viewable', True)
    # Allows a value to be assigned to this column via another name
    self.alias = kwargs.pop('alias', None)
    super().__init__(*args, **kwargs)

class BaseModel(db.Model):
  __abstract__ = True
  __mapper_args__ = {
    'extension' : Validator()
  }

  id = db.Column(db.BigInteger, primary_key=True)
  created_by = db.Column(db.BigInteger)
  created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())
  last_modified_by = db.Column(db.BigInteger)
  last_modified_at = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())

  @property
  def attributes(self):
    return [self.get_column_name(col) for col in self.get_discoverable_columns()]

  @property
  def create_attributes(self):
    return [self.get_column_name(col) for col in self.get_createable_columns()]

  @property
  def update_attributes(self):
    return [self.get_column_name(col) for col in self.get_updateable_columns()]

  def validate(self):
    pass

  def before_insert(self):
    # Ensure required columns are not null
    for required_column in self.get_required_columns():
      self.check_column_for_null(required_column)

  def before_update(self):
    pass

  def after_update(self):
    pass

  def before_delete(self):
    pass

  def after_delete(self):
    pass

  def get_column_name(self, column):
    return column.name if not hasattr(column, 'alias') or column.alias is None else column.alias

  def get_viewable_columns(self):
    return [col for col in self.__table__.columns if self.allowed_by_attribute(col, 'viewable')]

  def get_createable_columns(self):
    return [col for col in self.__table__.columns if not col.primary_key and self.allowed_by_attribute(col, 'createable')]

  def get_updateable_columns(self):
    return [col for col in self.__table__.columns if not col.primary_key and self.allowed_by_attribute(col, 'updateable')]

  def get_discoverable_columns(self):
    return [col for col in self.__table__.columns if self.allowed_by_attribute(col, 'discoverable')]

  def allowed_by_attribute(self, col, attribute_name):
    """
    This function validates the value of the metadata attributes defined on our custom Column class.
    It allows either a boolean or string. If a string is used, it is assumed to be the company instance type
    and will be validated against the current user's company context. If there is a match, the record's company must match
    the current user's company context.
    """
    if not hasattr(col, attribute_name):
      return False

    attribute_value = getattr(col, attribute_name)
    if not isinstance(attribute_value, bool) and not isinstance(attribute_value, str):
      raise ValidationException("Invalid value for '{}' model column '{}', attribute '{}'. Value must be a boolean or string".format(self.__class__.__name__, col.name, attribute_name))

    if isinstance(attribute_value, bool) and not attribute_value:
      return False

    if isinstance(attribute_value, str):
      # If the value is a string, it should either be 'cc' or 'studio' and indicates only viewable for that company type
      if attribute_value != g.user['company']['instanceType']:
        return False


      # If we're evaluating the viewable attribute, also make sure the record's company_id (if exists) matches current user's company
      if attribute_name == 'viewable' and hasattr(self, 'company_id') and self.company_id != g.user['company']['id']:
        return False

    return True

  def get_required_columns(self):
    return [col for col in self.__table__.columns if not col.nullable and col.name != 'id']

  def to_json(self):
    payload = {
        'id': self.id,
        'createdBy': self.created_by,
        'createdAt': self.created_at,
        'lastModifiedBy': self.last_modified_by,
        'lastModifiedAt': self.last_modified_at
    }

    for col in self.get_viewable_columns():
      # Need to look for "getter" method?
      property_name = underscore_to_camel(col.name)
      if hasattr(col, 'alias') and col.alias is not None:
        property_name = underscore_to_camel(col.alias)
      payload.update({ property_name: getattr(self, col.name) })

    return payload

  @property
  def id_validator(self):
    return util.IntValidator('id', min=0)

  def check_for_null(self, prop):
    if getattr(self, prop) == None:
      raise ValidationException("Expected value", api_field=underscore_to_camel(prop))

  def check_column_for_null(self, col):
    if getattr(self, col.name) == None:
      raise ValidationException("Expected value", api_field=underscore_to_camel(self.get_column_name(col)))


  def _get_current_container():
    return request.headers.get("Container-Id")

  @classmethod
  def get_last_by_old_id(cls):
    return cls.get_all().order_by(desc(cls.old_id)).first()