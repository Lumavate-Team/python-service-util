from ..models import ContentCategoryMediaAssetModel
from .content_category_media_asset_rest import ContentCategoryMediaAssetRestBehavior
from .filetype_category_rest import FileTypeCategoryRestBehavior
from lumavate_exceptions import ValidationException

class AssetFileTypeRestBehavior(ContentCategoryMediaAssetRestBehavior):
  def __init__(self, model_class=ContentCategoryMediaAssetModel, data=None):
    super().__init__(model_class, data, 'filetype')

  def set_asset_filetype(self, asset_id, filetype):
    if not filetype:
      raise ValidationException('No file type specified')
    
    self.delete_by_asset(asset_id)

    tag = FileTypeCategoryRestBehavior().get_tag_by_name(filetype)
    if not tag:
      raise ValidationException('File type not found')

    self.create_asset_category(asset_id, tag.id)
    