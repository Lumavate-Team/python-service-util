from sqlalchemy import or_, cast, VARCHAR, func
from app import db
import os
import re
import json
from ..models import CategoryModel
from .category_rest import CategoryRestBehavior

class TagRestBehavior(CategoryRestBehavior):
  def __init__(self, model_class=CategoryModel, data=None):
    super().__init__(model_class, data, 'tag')

  def batch_tags(self):
    data = self.get_data().get('data', [])
    response = []

    for tag in data:
      operation = tag.get('operation', '')
      if not operation:
        continue

      tag['type'] = 'tag'
      handler = CategoryRestBehavior(data=tag, category_type='tag')

      if operation == 'add':
        response.append(handler.post())
      if operation == 'modify':
        response.append(handler.put(tag['id']))
      if operation == 'delete':
        response.append(handler.delete(tag['id']))

    return response
  
  def get_asset_tags(self, asset_id):
    return self._model_class.get_by_asset_id(asset_id)