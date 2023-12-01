from sqlalchemy import or_, cast, VARCHAR, func
from app import db
import os
import re
import json
from ..models import create_asset_category_model
from ...rest import RestBehavior
from lumavate_exceptions import NotFoundException, InvalidOperationException

class AssetCategoryRestBehavior(RestBehavior):
  def __init__(self, model_class=create_asset_category_model(), data=None, category_type=''):
    self._category_type = category_type
    super().__init__(model_class, data)

  def get_by_asset(self, asset_id):
    if not self._category_type:
      return self._model_class().get_all_by_asset(asset_id)

    return self._model_class().get_all_by_type_and_asset(self._category_type, asset_id)

  def delete_by_asset(self, asset_id):
    if not self._category_type:
      return self._model_class().delete_all_by_asset(asset_id)

    return self._model_class().delete_all_by_type_and_asset(self._category_type, asset_id)

  def get_categories_by_asset(self, asset_id):
    if not self._category_type:
      return self._model_class.get_categories_by_asset(asset_id)

    return self._model_class.get_categories_by_type_and_asset(self._category_type, asset_id)

  def create_asset_category(self, asset_id, category_id):
    self.data = {'assetId': asset_id, 'categoryId': category_id, 'orgId': self.get_org_id()}
    return self.create()




