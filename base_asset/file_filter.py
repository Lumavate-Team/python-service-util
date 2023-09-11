from sqlalchemy.sql.expression import cast
import sqlalchemy.dialects.postgresql
from sqlalchemy import or_, String, and_, func, select
from flask import request, g
from dateutil.parser import parse
from lumavate_exceptions import ValidationException
from sqlalchemy.inspection import inspect
from ..filter import Filter
from .models import AssetCategoryModel, CategoryModel
import re

class FileFilter(Filter):
  def __init__(self, args=None, ignore_fields=None):
    super().__init__(args, ignore_fields)

  def apply_column(self, base_query, column_name, op, value):
    if op == 'ct' and column_name == 'name':
      column = self.get_column(base_query, column_name)
      filename_column = self.get_column(base_query, 'filename')
      clauses = [
        cast(filename_column, String).ilike('%' + value.strip() + '%'),
        cast(column, String).ilike('%' + value.strip() + '%')
      ]
      return base_query.filter(or_(*[c for c in clauses]))
      
    if op == 'eq' and column_name == 'tags':
      values = value.split('||')

      return base_query.filter(\
        self.get_column(base_query, 'id').\
          in_(AssetCategoryModel.get_all_by_type_and_ids('tag', values).with_entities(AssetCategoryModel.asset_id)))

    if op == 'eq' and column_name == 'filetype':
      values = value.split('||')

      return base_query.filter(\
        self.get_column(base_query, 'id').\
          in_(AssetCategoryModel.get_all_by_type_and_ids('filetype', values).with_entities(AssetCategoryModel.asset_id)))
    else:
      return super().apply_column(base_query, column_name, op, value)