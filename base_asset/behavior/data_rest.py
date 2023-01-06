from functools import partial
from flask import request
from sqlalchemy import Float, DateTime, desc
from ..models import DataBaseModel
from ..column import DataColumn
from ...rest import RestBehavior
from ...enums import ColumnDataType
from ...filter import Filter
from ...sort import Sort
from ..data_filter import DataRestFilter
from app import db

class DataRestSort(Sort):
  def __init__(self, model, asset_id):
    self.model = model
    schema_columns = self.model.get_column_definitions(asset_id)
    self.columns = {column_def.get('columnName'): DataColumn.from_json(column_def) for column_def in schema_columns}
    super().__init__()

  def apply_column(self,base_query, column_name, direction):
    if column_name in ['id', 'org_id' ,'asset_id','submitted_data', 'activation_code', 'is_draft', 'public_id','created_by' ,'created_at' ,'last_modified_by' ,'last_modified_at' ]:
      return super().apply_column(base_query, column_name, direction)

    if self.columns.get(column_name).column_type == 'numeric':
      column = self.model.submitted_data[column_name].astext.cast(Float)
    elif self.columns.get(column_name).column_type == 'datetime':
      column = self.model.submitted_data[column_name].astext.cast(DateTime)
    else:
      column = self.model.submitted_data[column_name].astext

    if direction == 'desc':
      column = desc(column)

    base_query = base_query.order_by(column)
    return base_query

class DataRestBehavior(RestBehavior):
  def __init__(self, asset_id, model_class=DataBaseModel, data=None, batch=False):
    self._asset_id = asset_id
    self.is_batch_request = batch
    super().__init__(model_class, data)

  def make_user_id(self, id):
    if id=='anonymous':
      id=-1
    return f'lmvt!{id}'

  def get_default_user_id(self):
    return 'lmvt!-1'

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
    try:
      self.apply_values(rec, {'submittedData': data})
      self.validate(rec)
    except Exception as e:
      db.session.expunge(rec)
      raise

    return rec

  def update_record(self, rec, data=None):
    try:
      self.apply_values(rec, data)
      self.validate(rec)
    except Exception as e:
      db.session.expunge(rec)
      raise

  def apply_sort(self, q):
    return DataRestSort(self._model_class, self._asset_id).apply(q)

  def apply_filter(self, q, ignore_fields=None):
    return DataRestFilter(self._model_class, self._asset_id, args=self.get_args(), ignore_fields=ignore_fields).apply(q)

  def get_collection_query(self):
    q = self._model_class.get_all_by_asset_id(self._asset_id, self.get_args())
    q = self.apply_filter(q)
    q = self.apply_sort(q)
    return q

  def get_rec_by_public_id(self, public_id):
    return self._model_class.get_by_public_id(self._asset_id, public_id)

  def create_public_id(self):
    pass

  def try_import_action(self, action_func, result_key, result_dict):
    try:
      action_func()
      result_dict[result_key] = result_dict[result_key] + 1
    except Exception as e:
      print(e,flush=True)
      result_dict['recordsFailed'] = result_dict['recordsFailed'] + 1
      pass

  def import_batch(self):
    file_input = self.get_batch_import_content()
    results = {
      'recordsAdded': 0,
      'recordsModified': 0,
      'recordsDeleted': 0,
      'recordsFailed': 0
    }
    if len(file_input) == 0:
      return results

    for row in file_input:
      data_rec = None
      action_key =None
      action = None
      row_data = dict(row)

      if row_data.get('lumavateId') == '' or row_data.get('lumavateId') is None:
        action_key = 'recordsAdded'
        action = partial(self.create_data_record, self._model_class, row_data)
      elif row_data.get('ACTION','') == 'DELETE':
        action_key = 'recordsDeleted'
        try:
          data_rec = self._model_class.get_by_public_id(self._asset_id, row_data['lumavateId'])
          if data_rec is None:
            raise Exception
        except Exception as e:
          print(f'Delete failed. Id: Data does not exist.\n{e}', flush=True)
          results['recordsFailed'] = results['recordsFailed'] + 1
          continue

        action = partial(self.delete, data_rec.id)
      else:
        action_key = 'recordsModified'
        try:
          data_rec = self._model_class.get_by_public_id(self._asset_id, row_data['lumavateId'])
        except Exception as e:
          print(f'Update failed. Id: Data does not exist.\n{e}', flush=True)
          results['recordsFailed'] = results['recordsFailed'] + 1
          continue

        action = partial(self.update_record, data_rec, {'submittedData': row_data})

      self.try_import_action(action, action_key, results)

    return results

  def get_ignored_properties(self):
    excluded_properties = ['createdBy', 'createdAt', 'lastModifiedBy', 'lastModifiedAt', 'activationCode', 'ACTION', 'lumavateId', 'namespace','orgId']

    if self.is_batch_request:
      column_defs = self._model_class.get_column_definitions(self._asset_id)
      file_columns = [ column['columnName'] for column in column_defs if column['columnType']['value'] == ColumnDataType.FILE]
      return [*excluded_properties, *file_columns]

    return excluded_properties

  def get_asset_fields(self):
    return ['submitted_data']
