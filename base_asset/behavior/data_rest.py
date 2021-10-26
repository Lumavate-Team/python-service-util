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
  def create_data_record(self, for_model, data):
    rec = super().create_record(for_model)
    rec.asset_id = self._asset_id
    rec.submitted_data = data
    self.apply_values(rec, {'submittedData': data})
    self.validate(rec)
    return rec

  def delete(self, record_id):
    if not db:
      raise Exception('Unable to validate record without db context')

    r = self._model_class.get_by_public_id(self._asset_id, record_id)
    result = self.pack(r)

    if r is not None:
      db.session.delete(r)
      result = r.to_json()

    return result

  def update_record(self, rec, data=None):
    self.apply_values(rec, data)
    self.validate(rec)

  def get_collection_query(self):
    q = self._model_class.get_all_by_asset_id(self._asset_id, self.get_args())
    q = self.apply_filter(q)
    q = self.apply_sort(q)
    return q

  def get_rec_by_public_id(self, public_id):
    return self._model_class.get_by_public_id(self._asset_id, public_id)

  def import_batch(self):
    file_input = self.get_batch_import_content()
    results = r
      'recordsAdded': 0,
      'recordsModified': 0,
      'recordsDeleted': 0,
      'recordsFailed': 0
    }
    if len(file_input) == 0:
      return results

    for row in file_input:
      data_rec = None
      row_data = None
      action_key =None

      if row.get('lumavateId') == '' or row.get('lumavateId') is None:
        action_key = 'recordsAdded'
        row_data = dict(row)
        action = partial(self.create_data_record, self._model_class, row_data)
      elif row.get('ACTION') == 'DELETE':
        action_key = 'recordsDeleted'
        action = partial(self.delete, row.get('lumavateId'))
      else:
        action = 'UPDATE'
        action_key = 'recordsModified'
        row_data = dict(row)
        try:
          data_rec = self._model_class.get_all_by_asset_id(self._asset_id, {'draft': False}).filter(self._model_class.public_id == row_data['lumavateId']).first()
        except Exception as e:
          print(f'Update failed. Id: Asset Id {self._asset_id} does not exist.', flush=True)
          results['recordsFailed'] = results['recordsFailed'] + 1
          continue

        action = partial(self.update_record, data_rec, {'submittedData': row_data})

      self._try_import_action(action, action_key, results)

      return results

    def get_ignored_properties(self):
      return ['createdBy', 'createdAt', 'lastModifiedBy', 'lastModifiedAt', 'activationCode', 'ACTION', 'lumavateId', 'namespace','orgId']

    def _try_import_action(self, action_func, result_key, result_dict):
      try:
        action_func()
        result_dict[result_key] = result_dict[result_key] + 1
      except ValidationException as e:
        print(f'Validation Exception\n{e}',flush=True)
        result_dict['recordsFailed'] = result_dict['recordsFailed'] + 1
      except Exception as e:
        print(f'Exception\n{e}',flush=True)
        result_dict['recordsFailed'] = result_dict['recordsFailed'] + 1
