from ...models import ImageAssetImageCategoryModel
from ..asset_tag_rest import AssetTagRestBehavior

class ImageAssetTagRestBehavior(AssetTagRestBehavior):
  def __init__(self, model_class=ImageAssetImageCategoryModel, data=None):
    super().__init__(model_class, data, 'tag')