from sqlalchemy import or_, cast, VARCHAR, func
import json
from ..models import create_asset_category_model
from .asset_category_rest import AssetCategoryRestBehavior
from ...rest import RestBehavior

class AssetTagRestBehavior(AssetCategoryRestBehavior):
  def __init__(self, model_class=create_asset_category_model(), data=None, category_type='tag'):
    super().__init__(model_class, data, category_type)

  def update_asset_tags(self, asset_id):
    data = self.get_data()
    existing_tags = {ac.category_id: ac.id for ac in self.get_by_asset(asset_id)}
    current_tags = data.get('tags', [])
    added_tags = []
    deleted_tags = []

    for tag in current_tags:
      if tag not in existing_tags:
        added_tags.append(tag)
    
    for tag in existing_tags.keys():
      if tag not in current_tags:
        deleted_tags.append(tag)

    for tag_id in added_tags:
      self.create_asset_category(asset_id, tag_id)

    for tag_id in deleted_tags:
      self.delete(existing_tags[tag_id])

    return data