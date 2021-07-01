from sqlalchemy import desc, union_all, select
from flask import request
from .filter import ColumnResolver

class AssetSort:
  def __init__(self):
    pass

  def apply(self, base_query):
    if request.args.get('sort') is not None:
      for sort in request.args.get('sort').split(','):
        sort_args = (sort + ' asc').split(' ')
        base_query = self.apply_column(base_query, sort_args[0], sort_args[1])
    else:
      base_query = self.apply_column(base_query, 'name', 'asc')

    return base_query

  def apply_column(self, base_query, column_name, direction):
    column = ColumnResolver(base_query._primary_entity.type().__mapper__).resolve(column_name)

    if column is not None:
      if direction == 'desc':
        column = desc(column)

      base_query = base_query.order_by(column)

    return base_query
