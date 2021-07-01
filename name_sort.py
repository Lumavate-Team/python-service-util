from sqlalchemy import desc, union_all, select
from flask import request
from .filter import ColumnResolver
from .sort import Sort

class NameSort(Sort):
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
