from sqlalchemy import update, select, func, case, cast, literal_column, and_, column,union, Text, join
from sqlalchemy.orm import load_only
from sqlalchemy.dialects.postgresql import JSONB, ARRAY,aggregate_order_by
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.sql.expression import Grouping
from .column import DataColumn
from ..column_select import ColumnSelect
from app import db
from ..filter import ColumnResolver

class DataRestSelect(ColumnSelect):
  def __init__(self, asset_id, model_class, columns=[], args=None):
    self.data_columns = columns
    self.model = model_class
    self.asset_id = asset_id
    self.data_column_names = {column_def.get('columnName') for column_def in self.data_columns}

    super().__init__(model_class=model_class, args=args)

  def convert_model_names(self, field_list):
    model_columns = super().convert_model_names(field_list)

    data_column_list = [column for column in self.data_column_names if column in field_list ]
    
    return model_columns + data_column_list

  def get_column_list(self):
    filtered_model_columns = super().get_column_list()
    
    data_columns = self.data_column_names

    # if any included_fields are specified then column list is based off the excplicit includes - excluded fields
    if len(self.included_fields) > 0:
      data_columns = self.included_fields

    if len(self.excluded_fields) > 0:
      data_columns = self.diff(data_columns, self.excluded_fields)

    filtered_data_columns = [dc for dc in data_columns if dc in self.data_column_names]

    return filtered_model_columns + filtered_data_columns

  def apply(self, base_query):
    if len(self.included_fields) == 0 and len(self.excluded_fields) == 0:
      return base_query
      
    column_list = self.get_column_list()
    data_column_list = []
    
    model_column_list = [self.resolve(base_query, column_name) for column_name in self.columns]
    for column_name in column_list:
      data_column_name = next((dc_name for dc_name in self.data_column_names if dc_name == column_name), None)
      if data_column_name is not None:
        data_column_list.append(column_name)
    
    if len(data_column_list) > 0:
      data_columns = func.jsonb_each(self.model.submitted_data)
      custom_data_columns = func.jsonb_each(self.model.submitted_data.op('->')('columns'))

      all_columns_cte = select([
        self.model.id,
        (Grouping(data_columns).op('.')(literal_column('key'))).cast(Text).label('key'),
        (Grouping(data_columns)).op('.')(literal_column('value')).cast(JSONB).label('value')
      ])\
      .select_from(self.model)\
      .cte('all_columns_cte')
      
      data_column_query = select([all_columns_cte.c.id, coalesce(func.jsonb_object_agg(all_columns_cte.c.key, all_columns_cte.c.value), cast({}, JSONB)).label('submitted_data')])\
        .select_from(all_columns_cte)\
        .where(all_columns_cte.c.key.in_(data_column_list))\
        .group_by(all_columns_cte.c.id)\
        .cte('data_columns_query_cte')

      all_custom_columns_cte = select([
        self.model.id,
        (Grouping(custom_data_columns).op('.')(literal_column('key'))).cast(Text).label('key'),
        (Grouping(custom_data_columns)).op('.')(literal_column('value')).cast(JSONB).label('value')
      ])\
      .select_from(self.model)\
      .cte('all_custom_columns_cte')
      
      data_custom_column_query = select([all_custom_columns_cte.c.id, coalesce(func.jsonb_object_agg(all_custom_columns_cte.c.key, all_custom_columns_cte.c.value), cast({}, JSONB)).label('columns')])\
        .select_from(all_custom_columns_cte)\
        .where(all_custom_columns_cte.c.key.in_(data_column_list))\
        .group_by(all_custom_columns_cte.c.id)\
        .cte('data_custom_columns_query_cte')
              
      # merge custom columns back into main submitted data returned columns
      query = select([data_column_query.c.id, 
                      func.jsonb_set(data_column_query.c.submitted_data, 
                                     '{columns}',
                                     coalesce(data_custom_column_query.c.columns, cast({}, JSONB))).label('submitted_data')])\
              .select_from(join(data_column_query, data_custom_column_query, data_custom_column_query.c.id == data_column_query.c.id, isouter=True))\
              .alias('filtered_submitted_data_columns')

      if 'submitted_data' not in model_column_list:
        model_column_list.append(query.c.submitted_data)

    return base_query.join(query, self.resolve(base_query, 'id')==query.c.id).with_entities(*model_column_list)

  def resolve(self, base_query, column_name):
    return ColumnResolver(base_query._primary_entity.type().__mapper__).resolve(column_name)
