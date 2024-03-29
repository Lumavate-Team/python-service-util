from sqlalchemy import or_, cast, VARCHAR, func, Float
from sqlalchemy.inspection import inspect
import json

from app import db
from .util import camel_to_underscore


class ColumnSelect:
  def __init__(self, model_class, args=None):
    self.columns = [key for key in model_class.__mapper__.columns.keys()]

    self.args = args
    self.included_fields = self.convert_arg_model_names('fields')
    self.excluded_fields = self.convert_arg_model_names('excludeFields')


  def convert_arg_model_names(self, select_arg):
    arg = self.args.get(select_arg,None)
    if arg is None:
      return []

    return self.convert_model_names(arg.split(','))


  def convert_model_names(self, field_list):
    if len(field_list) == 0:
      return field_list

    """
    Checks if columns and data fields in the select_arg are main Model columns(underscore_case) or a field(camelCase) and returns modified list
    in correct column/field syntax. But first filter columns to only columns that actually exist(prevent typos from returning)
    """
    field_list = list(filter(lambda item: self.to_underscore(item) in self.columns, field_list))
    return [self.to_underscore(item) if self.to_underscore(item) in self.columns else item for item in field_list]

  def to_underscore(self, field):
    return camel_to_underscore(field)

  def diff(self,list1, list2):
    s = set(list2)
    return [x for x in list1 if x not in list2]

  def get_column_list(self):
    # get all columns
    fields = self.columns

    # if any included_fields are specified then column list is based off the excplicit includes - excluded fields
    if len(self.included_fields) > 0:
      fields = self.included_fields

    if len(self.excluded_fields) > 0:
      fields = self.diff(fields, self.excluded_fields)

    return [field for field in fields if field in self.columns]

  def apply(self, base_query):
    if len(self.included_fields) == 0 and len(self.excluded_fields) == 0:
      return base_query
      
    column_list = self.get_column_list()
    return base_query.with_entities(*column_list)
