from jinja2 import Environment, BaseLoader
from flask import Blueprint, jsonify, request, make_response, redirect, render_template, g, abort
from lumavate_properties import Properties, Components, ColumnDataType
from lumavate_exceptions import ValidationException, NotFoundException
from sqlalchemy import or_, cast, VARCHAR, func
from datetime import datetime
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
      base_columns = [DataColumn.from_json(c) for c in self.get_column_definitions(record_id, include_inactive=True) if c.get('baseProperty', False)]
      existing_columns = [DataColumn.from_json(c) for c in self.get_column_definitions(record_id, include_inactive=True)]
      column_names = {c.name: True for c in existing_columns}
      column_display_names = {c.display_name.lower(): True for c in base_columns}
      asset_data = request_json.get('data', {})
      column_components = asset_data.get('columns', [])

      forbidden_names = ['type', 'null', 'none', 'undefined']
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

        if component_data['columnName'].lower() in forbidden_names or component_data['columnDisplayName'] in forbidden_names:
            raise ValidationException('This field name cannot be used.', f'columns|{index}|columnDisplayName')

        if component_data['columnDisplayName'].lower() in column_display_names:
            # show the error on display name since column name isn't being displayed in the edit
            raise ValidationException('Column Name is already in use.', f'columns|{index}|columnDisplayName')


        # add columnName to dictionary for unique name check
        column_names[component_data['columnName']] = True
        column_display_names[component_data['columnDisplayName'].lower()] = True

        if existing_column and component_data['columnType']['value'] != existing_column.column_type:
          raise ValidationException('Cannot change data type on an existing column.', f'columns|{index}|columnDisplayName')

      #parse and validate property data
      data = self._read_property_values(asset_data)
      data.pop('columnType', None)
      data.pop('columnDisplayName', None)
      request_json['data'] = data

      # compare data and see if anything has changed, otherwise just return so lastModified isn't updated
      existing_data = self._model_class.get(record_id).to_json().get('data', {})

      if existing_data == data:
        return {
          'state': 'cancelled',
          'payload': {'data': None}
          }

      if self._is_table_changed(data, existing_columns):
        request_json['schema_last_modified_at'] = datetime.utcnow()

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
    luma_columns = []
    if request.args.get('showLuma'):
      luma_columns = self.convert_properties_to_data_columns(self.get_luma_properties(), is_metadata=True)

    return luma_columns + self._model_class.get_column_definitions(record_id, include_inactive=include_inactive)

  # Converts the initial column display name to lowercase snake case after
  # removing all non alphanumeric characters
  def generate_column_name(self, component_data, row_index):
    column_display_name = component_data.get('columnDisplayName', '')
    sanitized = re.sub('[^a-zA-Z0-9]+', '_', column_display_name).lower()
    if bool(re.match('^.*(?=.*[a-zA-Z]|[0-9]).*$', sanitized)) == False:
      raise ValidationException('Column name must contain at least one letter or number.', api_field=f'columns|{row_index}|columnDisplayName')

    return sanitized.strip('_')

  def get(self, record_id):
    return self._model_class.get(record_id)

  # This converts a base property to a custom column definition which are used on field selections(asset-field-selector)
  def convert_properties_to_data_columns(self, properties, is_metadata=False):
    columns = []
    for prop in properties:
      if prop.property_type.type_name == 'dynamic-property-list':
        column_type_value = self.get_column_type(prop.options.get('propertyDef', {}).get('type', None))
        if column_type_value:
          column_type_value = 'dynamic-property-list:' + column_type_value
      else:
        column_type_value = self.get_column_type(prop.property_type.type_name)

      if column_type_value is None:
        continue

      columns.append({
        'columnDisplayName': prop.label, 
        'columnName': prop.name, 
        'columnType': {
          'value': column_type_value,
          'options': self.get_column_property_options(column_type_value, prop)
        },
        'id': None, 
        'isActive': True, 
        'baseProperty': True,
        'isMetadata': is_metadata
      })

    return columns

  def get_luma_properties(self):
    return [
      Properties.Property(None, None, 'publicId', 'ID', 'text', options={}),
      Properties.Property(None, None, 'createdAt', 'Created At', 'text', options={}),
      Properties.Property(None, None, 'lastModifiedAt', 'Last Modified At', 'text', options={}),
      Properties.Property(None, None, 'createdBy', 'Created By', 'text', options={}),
      Properties.Property(None, None, 'LastModifiedBy', 'Last Modified By', 'text', options={})
    ]
  
  def get_column_property_options(self, column_type, property):
    options = ''
    if column_type == ColumnDataType.DROPDOWN:
      options = ','.join([f'{key}|{value}' for key,value in property.options.items()])

    return options

  def get_column_type(self, property_type):
    types = {
      'asset-select': None,
      'asset-field': None,
      'text' : ColumnDataType.TEXT,
      'color': ColumnDataType.TEXT,
      'image-upload': ColumnDataType.IMAGE,
      'component': None,
      'components': None,
      'checkbox': ColumnDataType.BOOLEAN,
      'toggle': ColumnDataType.BOOLEAN,
      'translated-text': ColumnDataType.TEXT,
      'dropdown': ColumnDataType.DROPDOWN,
      'dropdown-options': None,
      'multiselect': None,
      'multiselect-chip': ColumnDataType.MULTISELECT,
      'numeric': ColumnDataType.NUMERIC,
      'page-link': ColumnDataType.DOCUMENT,
      'code-editor': None,
      'theme-color': ColumnDataType.TEXT,
      'admin-launcher': None,
      'html-editor': ColumnDataType.RICHTEXT,
      'html-editor-view': ColumnDataType.RICHTEXT,
      'simple-html-editor': ColumnDataType.RICHTEXT,
      'simple-html-editor-view': ColumnDataType.RICHTEXT,
      'dynamic-component': None,
      'dynamic-components': None,
      'dynamic-asset-select': None,
      'asset-data-select': ColumnDataType.ASSETDATA,
      'data-column-components': None,
      'data-column-row-input': None,
      'font': None,
      'file-upload': ColumnDataType.FILE,
      'email-list': ColumnDataType.TEXT,
      'font-style': None,
      'font-style-selector': None,
      'dynamic-property-list':None,
      'datetime': ColumnDataType.DATETIME, #doesn't exist yet
      'video': ColumnDataType.VIDEO #doesn't exist yet
    }

    return types.get(property_type)

