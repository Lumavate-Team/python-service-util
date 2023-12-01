from ...models import VideoAssetVideoCategoryModel
from ..asset_tag_rest import AssetTagRestBehavior

class VideoAssetTagRestBehavior(AssetTagRestBehavior):
  def __init__(self, model_class=VideoAssetVideoCategoryModel, data=None):
    super().__init__(model_class, data, 'tag')