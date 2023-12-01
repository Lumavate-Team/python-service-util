from ...models import AudioAssetAudioCategoryModel
from ..asset_tag_rest import AssetTagRestBehavior

class AudioAssetTagRestBehavior(AssetTagRestBehavior):
  def __init__(self, model_class=AudioAssetAudioCategoryModel, data=None):
    super().__init__(model_class, data, 'tag')