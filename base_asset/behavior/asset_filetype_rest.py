from ..models import create_asset_category_model
from ..models import create_category_model
from .asset_category_rest import AssetCategoryRestBehavior
from .filetype_category_rest import FileTypeCategoryRestBehavior
from lumavate_exceptions import ValidationException

class AssetFileTypeRestBehavior(AssetCategoryRestBehavior):
  def __init__(self, model_class=create_asset_category_model(), data=None, category_type='filetype', category_model_class=create_category_model()):
    self.category_model_class = category_model_class
    super().__init__(model_class, data, category_type)

  def set_asset_filetype(self, asset_id, filetype):
    if not filetype:
      raise ValidationException('No file type specified')
    
    self.delete_by_asset(asset_id)

    tag = FileTypeCategoryRestBehavior(model_class=self.category_model_class).get_tag_by_name(filetype)
    if not tag:
      raise ValidationException('File type not found')

    self.create_asset_category(asset_id, tag.id)
    