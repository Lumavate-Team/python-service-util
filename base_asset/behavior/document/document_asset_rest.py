import rollbar
from ...models import DocumentAssetModel
from ..file_asset_rest import FileAssetRestBehavior
from .document_asset_filetype_rest import DocumentAssetFileTypeRestBehavior
from .document_asset_tag_rest import DocumentAssetTagRestBehavior

class DocumentAssetRestBehavior(FileAssetRestBehavior):
  def __init__(self, model_class=DocumentAssetModel, data=None, file_mapping={}):
    self._filetype_category_mapping = file_mapping
    super().__init__(model_class, data)

  def set_asset_filetype(self, asset_id, filetype):
    if filetype in self._filetype_category_mapping:
      filetype = self._filetype_category_mapping[filetype]
    DocumentAssetFileTypeRestBehavior().set_asset_filetype(asset_id, filetype)
  
  def update_user_tags(self, data, asset_id):
    if not data or not isinstance(data, dict) or not 'tags' in data or not self.supports_tags():
      return data

    return DocumentAssetTagRestBehavior(data=data).update_asset_tags(asset_id)
  
  def pack(self, rec):
    if rec is None:
      return {}

    if type(rec) is self._model_class:
      json = rec.to_json()
      if self.expanded('tags') and self.supports_tags():
        json['expand'] = {}
        tags = DocumentAssetTagRestBehavior().get_categories_by_asset(rec.id)
        json['expand']['tags'] = [tag.to_json() for tag in tags]

      return json
    else:
      return {self.underscore_to_camel(key):value for(key,value) in rec._asdict().items()}