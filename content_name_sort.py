from sqlalchemy import desc, func, literal_column
from flask import request
from .filter import ColumnResolver
from .sort import Sort

class ContentNameSort(Sort):
  def __init__(self):
    super().__init__()

  def apply(self, base_query):
    if request.args.get('sort') is not None:
      for sort in request.args.get('sort').split(','):
        sort_args = (sort + ' asc').split(' ')
        base_query = self.apply_column(base_query, sort_args[0], sort_args[1])
    else:
      base_query = self.apply_column(base_query, 'name', 'asc')

    return base_query

  def apply_column(self, base_query, column_name, direction):
    column_whitelist = ['name', 'filename'];

    if column_name is not None and column_name in column_whitelist:
      column_name = func.lower(literal_column(column_name))
      if direction == 'desc':
        column_name = desc(column_name)

      base_query = base_query.order_by(column_name)

    return base_query