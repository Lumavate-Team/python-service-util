from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
import os
import re
import json
from lumavate_properties import Properties, Components
from lumavate_exceptions import ValidationException, ApiException
from app import db
from ...rest import RestBehavior
from ...request import LumavateRequest
from ...resolver import Resolver
from ...paging import Paging
from ...name_sort import NameSort
from ..models import AssetBaseModel
from ..models import SettingsModel
from ...util import camel_to_underscore, underscore_to_camel

class SettingsRestBehavior(RestBehavior):
  def __init__(self, model_class=SettingsModel, properties=None, data=None):
    super().__init__(model_class, data)
    self.properties = properties

  def make_user_id(self, id):
    return f'lmvt!{id}'

  def get_default_user_id(self):
    return 'lmvt!-1'

  def get_org_settings(self):
    settings_rec = self._model_class.get_org_settings()
    settings_json = {}
    if settings_rec:
      settings_json = self.pack(settings_rec).get('data',{})

    return {
        'properties': self.properties,
        'data': settings_json
        }

  def save_org_settings(self):
    settings_data = self.get_data()
    if 'data' not in settings_data:
      raise ApiException(500, 'Invalid request')

    settings_rec = self._model_class.get_org_settings()
    if settings_rec is None:
      post_data = {
        'orgId': self.get_org_id(),
        'data': settings_data['data']
      }

      self.data = post_data
      return self.post()
    else:
      self.data = settings_data
      return self.put(settings_rec.id)

  def get_org_setting(self, key):
    settings_rec = self._model_class.get_org_settings()
    if not settings_rec:
      return None

    return settings_rec.data.get(key, None)

  def delete_org(self, org_id):
    SettingsModel.delete_org(org_id)
