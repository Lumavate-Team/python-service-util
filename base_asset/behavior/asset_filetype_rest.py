from sqlalchemy import or_, cast, VARCHAR, func
import json
from ..models import AssetCategoryModel
from .asset_category_rest import AssetCategoryRestBehavior
from .content_category_rest import ContentCategoryRestBehavior
from ...rest import RestBehavior
from lumavate_exceptions import ValidationException

class AssetFileTypeRestBehavior(AssetCategoryRestBehavior):
  def __init__(self, model_class=AssetCategoryModel, data=None):
    super().__init__(model_class, data, 'filetype')

  def set_asset_filetype(self, asset_id, filetype):
    if not filetype:
      raise ValidationException('No file type specified')
    
    self.delete_by_asset(asset_id)

    tag = ContentCategoryRestBehavior().get_tag_by_name(filetype)
    if not tag:
      raise ValidationException('File type not found')

    self.create_asset_category(asset_id, tag.id)
    