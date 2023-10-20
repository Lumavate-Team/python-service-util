from sqlalchemy import or_, cast, VARCHAR, func
import json
from ..models import ContentCategoryModel
from ..models import ContentCategoryMediaAssetModel
from .asset_category_rest import AssetCategoryRestBehavior
from ...rest import RestBehavior

class ContentCategoryMediaAssetRestBehavior(AssetCategoryRestBehavior):
  def __init__(self, model_class=ContentCategoryMediaAssetModel, data=None):
    super().__init__(model_class, data, 'tag')

  def update_asset_tags(self, asset_id):
    data = self.get_data()
    existing_tags = {ac.content_category_id: ac.id for ac in self.get_by_asset(asset_id)}
    current_tags = data.get('tags', [])
    added_tags = []
    deleted_tags = []

    full_data = ContentCategoryModel.get_by_ids_and_type(current_tags, 'tag').all();
    
    for tag in full_data:
      if tag.id not in existing_tags:
        added_tags.append(tag.id)
    
    for tag in existing_tags.keys():
      if not any(current_tag.id == tag for current_tag in full_data):
        deleted_tags.append(tag)

    for tag_id in added_tags:
      self.create_asset_category(asset_id, tag_id)

    for tag_id in deleted_tags:
      self.delete(existing_tags[tag_id])

    return data
  
  def create_asset_category(self, asset_id, category_id):
    self.data = {'mediaAssetId': asset_id, 'contentCategoryId': category_id, 'orgId': self.get_org_id()}
    return self.create()