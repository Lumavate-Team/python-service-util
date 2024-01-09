from sqlalchemy.sql.expression import cast
import sqlalchemy.dialects.postgresql
from sqlalchemy import or_, String, and_, func, select
from flask import request, g
from dateutil.parser import parse
from lumavate_exceptions import ValidationException
from sqlalchemy.inspection import inspect
from ..filter import Filter
from .models import AssetCategoryModel
import re

class ContentFilter(Filter):
  def __init__(self, args=None, ignore_fields=None, model_class=AssetCategoryModel, asset_type=None):
    self._model_class=model_class
    self.asset_type = asset_type
    super().__init__(args, ignore_fields)

  def apply(self, base_query):
    ops = ['eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'sw', 'ct','aeq', 'adeq', 'act', 'any', 'in']
    search = {'columns': [], 'value': None}

    for a in self.args:
      if a != 'sort' and a not in self.ignore_fields:
        parts = self.args[a].split(":", 1)
        if len(parts) > 1 and parts[0] in ops:
          if self.asset_type is not None and a.startswith(self.asset_type + '_'):
            base_query = self.apply_column(base_query, a.replace(self.asset_type + '_', ''), parts[0], parts[1])
          else:
            base_query = self.apply_column(base_query, a, parts[0], parts[1])
        elif len(parts) > 1 and parts[0] == 'find':
          search['columns'].append(a)
          #the value should be the same across columns for search
          search['value'] = parts[1]        
        else:
          if self.asset_type is not None and a.startswith(self.asset_type + '_'):
            base_query = self.apply_column(base_query, a.replace(self.asset_type + '_', ''), 'eq', self.args[a])
          else:
            base_query = self.apply_column(base_query, a, 'eq', self.args[a])

    if len(search['columns']) > 0 and search['value'] is not None:
      search_clauses = [self.get_expression(column_name, self.get_column(base_query, column_name), 'ct', search['value']) \
                        for column_name in search['columns']]
      base_query = base_query.filter(or_(*[c for c in search_clauses if c is not None]))

    return base_query

  def apply_column(self, base_query, column_name, op, value):
    if op == 'ct' and column_name == 'name':
      column = self.get_column(base_query, column_name)
      filename_column = self.get_column(base_query, 'filename')
      clauses = [
        cast(filename_column, String).ilike('%' + value.strip() + '%'),
        cast(column, String).ilike('%' + value.strip() + '%')
      ]
      return base_query.filter(or_(*[c for c in clauses]))
      
    if op == 'eq' and column_name in ['tags', 'tag']:
      values = value.split('||')

      return base_query.filter(\
        self.get_column(base_query, 'id').\
          in_(self._model_class.get_all_by_type_and_ids('tag', values).with_entities(self._model_class.asset_id)))

    if op == 'eq' and column_name == 'filetype':
      values = value.split('||')

      return base_query.filter(\
        self.get_column(base_query, 'id').\
          in_(self._model_class.get_all_by_type_and_ids('filetype', values).with_entities(self._model_class.asset_id)))
    else:
      return super().apply_column(base_query, column_name, op, value)