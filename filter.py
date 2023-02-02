from sqlalchemy.sql.expression import cast
import sqlalchemy.dialects.postgresql
from sqlalchemy import or_, String, and_
from flask import request, g
from dateutil.parser import parse
from lumavate_exceptions import ValidationException
from sqlalchemy.inspection import inspect
import re
from .util import camel_to_underscore

class Filter:
  def __init__(self, args=None, ignore_fields=None):
    self.subs = {
      "@null": None
    }
    if ignore_fields:
      self.ignore_fields = ignore_fields
    else:
      self.ignore_fields = []

    self.args = args
    if args is None:
      self.args = request.args

    #Serialize all arg values to a string to be compatible with filters
    if self.args is not None:
      for arg_key in self.args:
        arg_value = self.args[arg_key]
        if isinstance(arg_value, list):
          self.args[arg_key] = '||'.join([str(v) for v in arg_value])
        elif not isinstance(arg_value, str):
          self.args[arg_key] = str(arg_value)

  def apply(self, base_query):
    ops = ['eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'sw', 'ct','aeq', 'adeq', 'act', 'in']
    for a in self.args:
      if a != 'sort' and a not in self.ignore_fields:
        parts = self.args[a].split(":", 1)
        if len(parts) > 1 and parts[0] in ops:
          base_query = self.apply_column(base_query, a, parts[0], parts[1])
        else:
          base_query = self.apply_column(base_query, a, 'eq', self.args[a])

    return base_query

  def apply_column(self, base_query, column_name, op, value):
    if op == 'aeq':
      clauses = [self.get_expression(column_name, self.get_column(base_query, column_name), op, value.split(','))]
    elif op == 'adeq':
      clauses = [self.get_expression(column_name, self.get_column(base_query, column_name), op, [int(x) for x in value.split(',')])]
    else:
      clauses = [self.get_expression(column_name, self.get_column(base_query, column_name), op, v) for v in value.split('||')]
    return base_query.filter(or_(*[c for c in clauses if c is not None]))

  def get_column(self, base_query, column_name):
    column = ColumnResolver(base_query._primary_entity.type().__mapper__).resolve(column_name)
    return column

  def get_expression(self, column_name, column, op, value):
    if isinstance(value, str) and value in self.subs:
      value = self.subs[value]

    original_value = value
    if isinstance(value, str) and value.lower() == '_null_':
      value = None

    if column is not None:
      if isinstance(column, sqlalchemy.dialects.postgresql.JSONB):
        pass
      if str(column.type) == 'DATETIME' or str(column.type) == 'DATE':
        value = parse(value)
      elif str(column.type) == 'BIGINT' or str(column.type) == 'INT':
        if op == 'in':
          value = str(value).split(',')
        else:
          value = int(str(value))
      elif str(column.type) == 'FLOAT':
        value = float(str(value))
      elif str(column.type) == 'BOOLEAN':
        value = str(value).lower() == 'true'
        if op != 'eq':
          raise ValidationException('Booleans can only be filtered using an equals operator', api_field=column_name)

      if op == 'eq':
        if str(column.type) == 'BIGINT[]':
          return column.any(value)
        else:
          return column == value
      elif op == 'neq':
        return column != value
      elif op == 'gt':
        return column > value
      elif op == 'gte':
        return column >= value
      elif op == 'lt':
        return column < value
      elif op == 'lte':
        return column <= value
      elif op == 'sw':
        return cast(column, String).ilike(original_value + '%')
      elif op == 'ct':
        return cast(column, String).ilike('%' + original_value + '%')
      elif op == 'aeq':
        return and_(column.op('@>')(value),column.op('<@')(value))
      elif op == 'adeq':
        return and_(column.op('@>')(value),column.op('<@')(value))
      elif op == 'act':
        return column.contains(value)
      elif op == 'in':
        return column.in_(value)


class ColumnResolver:
  def __init__(self, mapper):
    self.mapper = mapper

  def resolve(self, column_name):
    column_name = camel_to_underscore(column_name)
    column = None
    columns = inspect(self.mapper).columns
    if column_name in columns:
      column = columns[column_name]
      column = inspect(self.mapper).get_property_by_column(column).expression

    return column
