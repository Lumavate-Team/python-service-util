from sqlalchemy import Float, DateTime, desc, VARCHAR
from sqlalchemy.dialects.postgresql import ARRAY
from .column import DataColumn
from ..filter import Filter

class DataRestFilter(Filter):
  def __init__(self, model, asset_id, args=None, ignore_fields=None):
    self.model = model
    schema_columns = self.model.get_column_definitions(asset_id)
    self.columns = {column_def.get('columnName'): DataColumn.from_json(column_def) for column_def in schema_columns}
    super().__init__(args, ignore_fields)

  def get_column(self, base_query, column_name):
    if self.columns.get(column_name) is None:
      return super().get_column(base_query, column_name)

    if self.columns.get(column_name).column_type == 'numeric':
      return self.model.submitted_data['columns'][column_name].astext.cast(Float)
    elif self.columns.get(column_name).column_type == 'datetime':
      return self.model.submitted_data['columns'][column_name].astext.cast(DateTime)
    elif self.columns.get(column_name).column_type == 'multiselect':
      return self.model.submitted_data['columns'][column_name]
    else:
      return self.model.submitted_data['columns'][column_name].astext
