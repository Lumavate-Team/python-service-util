from sqlalchemy import or_, cast, VARCHAR, func
from app import db
import os
import re
import json
from ..models import CategoryModel
from .category_rest import CategoryRestBehavior
from lumavate_exceptions import InvalidOperationException

class StaticCategoryRestBehavior(CategoryRestBehavior):
  def __init__(self, model_class=CategoryModel, data=None, category_type=''):
    super().__init__(model_class, data, category_type)

  def post(self):
    raise InvalidOperationException('Category cannot be created')

  def put(self, record_id):
    raise InvalidOperationException('Category cannot be modified')

  def delete(self, record_id):
    raise InvalidOperationException('Category cannot be deleted')

  def get_tag_by_name(self, name):
    return self._model_class.get_by_name_and_type(name, self._category_type)