from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from sqlalchemy import or_, cast, VARCHAR, func
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
from ..models import AssetAccessBaseModel
from ...util import camel_to_underscore, underscore_to_camel

class AssetAccessRestBehavior(RestBehavior):
  def __init__(self, model_class=AssetAccessBaseModel, data=None):
    super().__init__(model_class, data)

  def make_user_id(self, id):
    return f'lmvt!{id}'

  def get_default_user_id(self):
    return 'lmvt!-1'

  def get_access(self, asset_id):
    access_rec = self._model_class.get_by_asset(asset_id)
    if access_rec:
      return self.pack(access_rec)

    return {}

  def save_access(self, asset_id):
    access_data = self.get_data()
    if 'operations' not in access_data:
      raise ApiException(500, 'Invalid request')

    access_rec = self._model_class.get_by_asset(asset_id, return_default=False)
    if access_rec is None:
      operations = access_data['operations']
      post_data = {
        'orgId': self.get_org_id(),
        'assetId': access_data['assetId'],
        'getAccess': operations['getAccess'],
        'postAccess': operations['postAccess'],
        'putAccess': operations['putAccess'],
        'deleteAccess': operations['deleteAccess']
      }

      self.data = post_data
      return self.post()
    else:
      self.data = access_data['operations']
      return self.put(access_rec.id)
