from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from lumavate_properties import Properties, Components
from lumavate_exceptions import ValidationException, NotFoundException
from sqlalchemy import or_, cast, VARCHAR, func
import itertools
from app import db
import os
import re
import json
from .asset_rest import AssetRestBehavior
from ..models import DataAssetBaseModel
from ..column import DataColumn

class DataAssetRestBehavior(AssetRestBehavior):
  def __init__(self, model_class=DataAssetBaseModel, data=None, properties=[]):
    super().__init__(model_class, data)
    self._properties = properties

  def put(self, record_id):
    column_names = {}
    column_display_names = {}

    request_json = self.get_data()
    if 'data' in request_json:
      existing_columns = [DataColumn.from_json(c) for c in self.get_column_definitions(record_id, include_inactive=True)]

      asset_data = request_json.get('data', {})
      column_components = asset_data.get('columns', [])
      for index, component in enumerate(column_components):
        component_data = component.get('componentData',{})

        # convert display name to column name, check for uniqueness
        component_data['columnDisplayName'] = component_data['columnDisplayName'].strip()
        existing_column = next((col for col in existing_columns if col.id == component_data['id']),None)

        if existing_column is None:
          component_data['columnName'] = self.generate_column_name(component_data, index)

          if component_data['columnName'] in column_names:
            # show the error on display name since column name isn't being displayed in the edit
            raise ValidationException('API Name is already in use.', f'columns|{index}|columnDisplayName')
        else:
          component_data['columnName'] = existing_column.name

        if component_data['columnDisplayName'] in column_display_names:
            # show the error on display name since column name isn't being displayed in the edit
            raise ValidationException('Column Name is already in use.', f'columns|{index}|columnDisplayName')


        # add columnName to dictionary for unique name check
        column_names[component_data['columnName']] = True
        column_display_names[component_data['columnDisplayName']] = True

        if existing_column and component_data['columnType']['value'] != existing_column.column_type:
          raise ValidationException('Cannot change data type on an existing column.', f'columns|{index}|columnDisplayName')

      #parse and validate property data
      data = self._read_property_values(asset_data)
      data.pop('columnType', None)
      data.pop('columnDisplayName', None)
      request_json['data'] = data

      # compare data and see if anything has changed, otherwise just return so lastModified isn't updated
      if not self._is_table_changed(data, existing_columns):
        return {
          'state': 'cancelled',
          'payload': {'data': None}
          }

    # update the data with added columnName field
    request_json['state'] = 'promoted'
    self.data = request_json

    response = super().put(record_id)
    return response

  def _read_property_values(self, asset_data):
    if asset_data is None:
       return {}

    column_prop = next((c for c in self._properties if c['name'] == 'columns'), None)
    if not column_prop:
      return {}

    column_component = next((c for c in column_prop.get('options',{}).get('components',[]) if c['type'] == 'column'), None)
    for index, column_data in enumerate(asset_data.get('columns',[])):
      component_data = column_data.get('componentData', None)
      for p in column_component['properties']:
        prop = Properties.Property.from_json(p)

        values = {p['name']: component_data.get(p['name'])}
        try:
          asset_data[prop.name] = prop.read(values)
        except ValidationException as e:
          print('validation exception ',e, flush=True)
          # wrap exception with id so error can show on correct row
          raise ValidationException(e.message, api_field=f'columns|{index}|{e.api_field}')
        except Exception as e:
          print('exception', e, flush=True)
          raise

    return asset_data

  def _is_table_changed(self, request_data, existing_columns):
    request_columns = [DataColumn.from_json(c.get('componentData')).__dict__ \
        if c.get('componentData') is not None else {} for c in request_data.get('columns',[])]
    existing_columns = [c.__dict__ for c in existing_columns]

    diff = list(itertools.filterfalse(lambda x: x in request_columns, existing_columns)) \
         + list(itertools.filterfalse(lambda x: x in existing_columns, request_columns))

    return len(diff) > 0

  def get_table_definition(self, record_id):
    asset = self._model_class.get(record_id)
    return {
      'columns': self.get_column_definitions(record_id),
      'lastModified': asset.last_modified_at
    }

  # return column definitions in easily consumable json format(remove unnecessary fields in response)
  def get_column_definitions(self, record_id, include_inactive=False):
    return self._model_class.get_column_definitions(record_id, include_inactive=include_inactive)

  # Converts the initial column display name to lowercase snake case after
  # removing all non alphanumeric characters
  def generate_column_name(self, component_data, row_index):
    column_display_name = component_data.get('columnDisplayName', '')
    sanitized = re.sub('\W+', '_', column_display_name).lower()
    if bool(re.match('^.*(?=.*[a-zA-Z]|[0-9]).*$', sanitized)) == False:
      raise ValidationException('Column name must contain at least one letter or number.', api_field=f'columns|{row_index}|columnDisplayName')

    return sanitized.strip('_')
