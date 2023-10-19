from sqlalchemy import or_, cast, VARCHAR, func
from app import db
import os
import re
import json
from ..models import CategoryModel
from ...rest import RestBehavior
from lumavate_exceptions import NotFoundException, InvalidOperationException

class CategoryRestBehavior(RestBehavior):
  def __init__(self, model_class=CategoryModel, data=None, category_type=''):
    self._category_type = category_type
    super().__init__(model_class, data)

  def get_collection_query(self):
    if self._model_class is None:
      return None

    q = None
    if not self._category_type:
      q = self._model_class.get_all(self._category_type)
    else:
      q = self._model_class.get_all_by_type(self._category_type)

    q = self.apply_filter(q)
    q = self.apply_sort(q)
    q = self.apply_select(q)
    return q


  def post(self):
    if not self._category_type:
      raise InvalidOperationException('Category type must be specified')

    data = self.get_data()
    data['type'] = self._category_type
    self.data = data
    
    return super().post()

  def put(self, record_id):
    record = self._model_class.get(record_id)

    if self._category_type and record.type != self._category_type:
      raise NotFoundException(404, '')

    return super().put(record_id)

  def delete(self, record_id):
    record = self._model_class.get(record_id)
    if self._category_type and record.type != self._category_type:
      raise NotFoundException(404, '')

    return super().delete(record_id)



