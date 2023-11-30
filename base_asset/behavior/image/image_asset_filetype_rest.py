from ...models import ImageAssetImageCategoryModel
from ..asset_filetype_rest import AssetFileTypeRestBehavior
from .image_filetype_category_rest import ImageFileTypeCategoryRestBehavior
from lumavate_exceptions import ValidationException

class ImageAssetFileTypeRestBehavior(AssetFileTypeRestBehavior):
  def __init__(self, model_class=ImageAssetImageCategoryModel, data=None, category_type='filetype'):
    super().__init__(model_class, data, category_type)

  def set_asset_filetype(self, asset_id, filetype):
    if not filetype:
      raise ValidationException('No file type specified')
    
    self.delete_by_asset(asset_id)

    tag = ImageFileTypeCategoryRestBehavior().get_tag_by_name(filetype)
    if not tag:
      raise ValidationException('File type not found')

    self.create_asset_category(asset_id, tag.id)
    