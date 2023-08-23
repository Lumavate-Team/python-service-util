from sqlalchemy import update, select, func, case, cast, literal_column, and_, column,union, Text
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

    #model_column_list = []
    data_column_list = []
    
    #model_column_list = self.columns
    model_column_list = [self.resolve(base_query, column_name) for column_name in self.columns]
    for column_name in column_list:
      """
      base_column = next((base_col_name for base_col_name in self.columns if base_col_name == column_name), None)
      if base_column is not None:
       model_column_list.append(base_column)
       continue
      """

      data_column_name = next((dc_name for dc_name in self.data_column_names if dc_name == column_name), None)
      if data_column_name is not None:
        data_column_list.append(column_name)
    
    # TODO: This should be a combination of main table columns(with_entities) and asset data columns queries
    # return query based on which arrays have values

    #return base_query.with_entities(*base_column_list)
    if len(data_column_list) > 0:
      print(f'GOT HERE',flush=True)
      """
      select jsonb_object_agg(v.key, case when jsonb_typeof(v.value) = 'object' 
      then jsonb_build_object('name', v.value -> 'name', 'age', v.value -> 'age') 
      else (select jsonb_agg(jsonb_build_object('name', v1.value -> 'name', 
                'age', v1.value -> 'age')) 
              from jsonb_array_elements(v.value) v1) end) 
      from tbl t cross join jsonb_each(t.js::jsonb) v

      """
      data_columns = func.jsonb_each(self.model.submitted_data)
      print(f'B: {base_query}',flush=True)

      all_columns_cte = select([
        self.model.id,
        (Grouping(data_columns).op('.')(literal_column('key'))).cast(Text).label('key'),
        (Grouping(data_columns)).op('.')(literal_column('value')).cast(JSONB).label('value')
      ])\
      .select_from(self.model)\
      .cte('component_properties_cte')
      
      data_column_query = select([all_columns_cte.c.id, all_columns_cte.c.key, all_columns_cte.c.value])\
        .select_from(all_columns_cte)\
        .where(all_columns_cte.c.key.in_(data_column_list))\
        .alias('data_columns_query')

      query = select([data_column_query.c.id, coalesce(func.jsonb_object_agg(data_column_query.c.key, data_column_query.c.value), cast({}, JSONB)).label('submitted_data')])\
              .select_from(all_columns_cte) \
              .group_by(data_column_query.c.id)\
              .alias('submitted_data_query')
              
      result = db.session.execute(query)
      for r in result:
        print(f'R: {r}',flush=True)
    #result_query = base_query.with_entities(*model_column_list)
      if 'submitted_data' not in model_column_list:
        model_column_list.append(query.c.submitted_data)
    #model_column_list.append('data_id')
    print(f"B: {base_query}",flush=True)

    """
    result_query = base_query\
      .join(query)\
      .values(*model_column_list)
    """
      #.with_entities(*model_column_list)
    """
    result_query = select([self.resolve(base_query,m) for m in model_column_list] + [query.c.submitted_data])\
                .select_from(base_query)\
                .join(query, column('id')==query.c.id) 
    """
    result_query = base_query.join(query, self.resolve(base_query, 'id')==query.c.id).with_entities(*model_column_list)

    print(f'QQQ: {result_query}',flush=True)

    return result_query
    #return base_query.options(load_only(*base_column_list)) #with_entities(*column_list)

    """

    def apply_column(self,base_query, column_name, direction):
      if column_name in ['id', 'org_id' ,'asset_id','submitted_data', 'activation_code', 'is_draft', 'public_id','created_by' ,'created_at' ,'last_modified_by' ,'last_modified_at' ]:
        return super().apply_column(base_query, column_name, direction)

      column = self.columns.get(column_name)
      if column is not None:
        if column.column_type == 'numeric':
          column = self.model.submitted_data['columns'][column_name].astext.cast(Float)
        elif column.column_type == 'datetime':
          column = self.model.submitted_data['columns'][column_name].astext.cast(DateTime)
        else:
          column = self.model.submitted_data['columns'][column_name].astext
      else:
        column = self.model.submitted_data[column_name].astext

      if direction == 'desc':
        column = desc(column)

      base_query = base_query.order_by(column)
      return base_query
    """
  def resolve(self, base_query, column_name):
    return ColumnResolver(base_query._primary_entity.type().__mapper__).resolve(column_name)
