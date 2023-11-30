from ..models import AssetCategoryModel
from .asset_category_rest import AssetCategoryRestBehavior
from .filetype_category_rest import FileTypeCategoryRestBehavior
from lumavate_exceptions import ValidationException

class AssetFileTypeRestBehavior(AssetCategoryRestBehavior):
  def __init__(self, model_class=AssetCategoryModel, data=None, category_type='filetype'):
    super().__init__(model_class, data, category_type)

  def set_asset_filetype(self, asset_id, filetype):
    if not filetype:
      raise ValidationException('No file type specified')
    
    self.delete_by_asset(asset_id)

    tag = FileTypeCategoryRestBehavior().get_tag_by_name(filetype)
    if not tag:
      raise ValidationException('File type not found')

    self.create_asset_category(asset_id, tag.id)
    