import rollbar
from ...models import DocumentAssetModel
from ..file_asset_rest import FileAssetRestBehavior
from ..asset_rest import AssetRestBehavior
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

  def post(self):
    asset_data = self.get_data()

    properties = self.get_asset_properties()
    asset_data = self.read_property_values(asset_data, properties)
    self.validate_asset_name(asset_data)
    asset_data = self.update_file_tags(asset_data)
    post_data = {
      'name': asset_data.get('assetName'),
      'orgId': self.get_org_id(),
      'isActive': True,
      'data': asset_data,
      'dependencyAssets': self.get_dependencies(asset_data)
    }
    filename = asset_data.get('file',{}).get('filename')
    # pull filename out into column for easy search query
    if filename:
      post_data['filename'] = filename

    self.data = post_data
    # skip asset rest since we already built up the post data
    result = super(AssetRestBehavior, self).post()

    self.update_user_tags(asset_data, result['id'])
    if self.supports_filetype_category():
      self.set_asset_filetype(result['id'], asset_data.get('file', {}).get('extension', ''))
  
    return result
  
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