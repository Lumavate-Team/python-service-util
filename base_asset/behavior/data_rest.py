from jinja2 import Environment, BaseLoader
from functools import partial
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from sqlalchemy import or_, cast, VARCHAR, func
from sqlalchemy.orm.attributes import flag_modified
import os
import re
import json
from lumavate_properties import Properties, Components
from lumavate_exceptions import ApiException, ValidationException, NotFoundException
from ..models import DataBaseModel
from ...rest import RestBehavior, Paging, camel_to_underscore, underscore_to_camel
from app import db

class DataRestBehavior(RestBehavior):
  def __init__(self, asset_id, data=None):
    self._asset_id = asset_id
    super().__init__(DataBaseModel, data)

  def post(self):
    data = self.get_data()
    host_split = request.host.split('.')
    data['isDraft'] = host_split[0].endswith("__test") or host_split[0].endswith("--test")
    self.data = data
    return super().post()

  def create_record(self, for_model):
    rec = super().create_record(for_model)
    rec.asset_id = self._asset_id
    rec.submitted_data = self.data.get('submittedData',{})
    return rec

  def get_collection_query(self):
    q = self._model_class.get_all_by_asset_id(self._asset_id, self.get_args())
    q = self.apply_filter(q)
    q = self.apply_sort(q)
    return q

  def get_rec_by_public_id(self, public_id):
    return self._model_class.get_by_public_id(self._asset_id, public_id)
