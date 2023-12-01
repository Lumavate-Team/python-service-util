import rollbar
from ...models import AudioAssetModel
from ..file_asset_rest import FileAssetRestBehavior
from .audio_asset_filetype_rest import AudioAssetFileTypeRestBehavior
from .audio_asset_tag_rest import AudioAssetTagRestBehavior

class AudioAssetRestBehavior(FileAssetRestBehavior):
  def __init__(self, model_class=AudioAssetModel, data=None, file_mapping={}):
    self._filetype_category_mapping = file_mapping
    super().__init__(model_class, data)

  def set_asset_filetype(self, asset_id, filetype):
    if filetype in self._filetype_category_mapping:
      filetype = self._filetype_category_mapping[filetype]
    AudioAssetFileTypeRestBehavior().set_asset_filetype(asset_id, filetype)
  
  def update_user_tags(self, data, asset_id):
    if not data or not isinstance(data, dict) or not 'tags' in data or not self.supports_tags():
      return data

    return AudioAssetTagRestBehavior(data=data).update_asset_tags(asset_id)
  
  def pack(self, rec):
    if rec is None:
      return {}

    if type(rec) is self._model_class:
      json = rec.to_json()
      if self.expanded('tags') and self.supports_tags():
        json['expand'] = {}
        tags = AudioAssetTagRestBehavior().get_categories_by_asset(rec.id)
        json['expand']['tags'] = [tag.to_json() for tag in tags]

      return json
    else:
      return {self.underscore_to_camel(key):value for(key,value) in rec._asdict().items()}