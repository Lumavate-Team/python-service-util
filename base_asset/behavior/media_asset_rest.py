from lumavate_exceptions import ApiException
import rollbar
from .asset_rest import AssetRestBehavior
from .asset_filetype_rest import AssetFileTypeRestBehavior
from ..models import MediaAssetModel
from .content_category_media_asset_rest import ContentCategoryMediaAssetRestBehavior
from ...aws import FileBehavior
from ..file_filter import FileFilter

class MediaAssetRestBehavior(AssetRestBehavior):
  def __init__(self, model_class=MediaAssetModel, data=None, file_mapping={}):
    self._filetype_category_mapping = file_mapping
    super().__init__(model_class, data)

  def supports_filetype_category(self):
    return False

  def get_asset_content(self, asset_id):
    asset = self._model_class.get(asset_id)
    return self._get_document_content(asset)

  def get_asset_content_by_public_id(self, public_id):
    asset = self._model_class.get_by_public_id(public_id)
    return self._get_document_content(asset)

  def _get_document_content(self, asset):
    if asset is None:
      return {}

    file = asset.data.get('file',{})
    image = {}
    # Document Asset Type content response has not been finalized
    return {
      'url': file['url'],
      'filename': file['filename'],
      'filetype': file['filetype'],
    }

  def apply_filter(self, q, ignore_fields=None):
    return FileFilter(self.args, ignore_fields).apply(q)

  def get_asset_properties(self):
    raise ApiException(500, "get asset properties not implemented")

  def set_asset_filetype(self, asset_id, filetype):
    if filetype in self._filetype_category_mapping:
      filetype = self._filetype_category_mapping[filetype]
    AssetFileTypeRestBehavior().set_asset_filetype(asset_id, filetype)

  def get_single(self, record_id):
    record_id = self.get_id(record_id)
    q = self.apply_filter(self._model_class.get_all()).filter(self._model_class.old_id == record_id)
    r = self.apply_select(q).first()
    return self.pack(r)

  def post(self):
    asset_data = self.get_data()

    properties = self.get_asset_properties()
    asset_data = self.read_property_values(asset_data, properties)
    self.validate_asset_name(asset_data)
    asset_data = self.update_file_tags(asset_data)

    lastCategory = self._model_class.get_last_by_old_id()
    
    post_data = {
      'name': asset_data.get('assetName'),
      'orgId': self.get_org_id(),
      'containerId': int(self._model_class._get_current_container()),
      'oldId': 1 if lastCategory == None else lastCategory.old_id+1,
      'assetType': self.get_asset_type(),
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
    rec = self.create_record(self._model_class)
    self.apply_values(rec)
    self.validate(rec)
    result = self.pack(rec)
    self.update_user_tags(asset_data, result['id'])
    if self.supports_filetype_category():
      self.set_asset_filetype(result['id'], asset_data.get('file', {}).get('extension', ''))
  
    return result

  def put(self, record_id):
    record = self.get_single(record_id)
    original_path = record.get('data',{}).get('file',{}).get('path','')

    asset_update_data = self.get_data()
    asset_data = asset_update_data.get('data', {})

    properties = self.get_asset_properties()
    asset_update_data['data'] = self.read_property_values(asset_data, properties)
    file = asset_update_data['data'].get('file',{})

    # pull filename out into column for easy search query
    if file.get('filename'):
      asset_update_data['filename']=file['filename']

    self.data = asset_update_data
    asset_update_data = self.get_data()
    asset_data = asset_update_data.get('data', {})

    self.validate_asset_name(asset_data, record['id'])
    asset_data = self.update_user_tags(asset_data, record['id'])
    asset_update_data['data'] = self.update_file_tags(asset_data)
    self.data = asset_update_data
    if 'assetName' in asset_data:
      self.data['name'] = asset_data['assetName']

    self.data['dependencyAssets'] = self.get_dependencies(asset_update_data)

    record_id = self.get_id(record_id)
    rec = self._model_class.get(record_id)

    self.apply_values(rec)
    self.validate(rec)
    response_data = self.pack(rec)

    response = {
      'state': asset_update_data.get('state', 'promoted'),
      'payload': response_data
    }

    if self.supports_filetype_category():
      self.set_asset_filetype(record_id, file.get('extension'))

    # delete the old file when a new one is uploaded
    if file and file.get('path','') != original_path:
      FileBehavior().delete(original_path)

    return response

  def delete(self, record_id):
    # Delete s3 object
    record = self.get_single(record_id)
    file_path = record.get('data',{}).get('file',{}).get('path','')
    if file_path:
      try:
        FileBehavior().delete(file_path)
      except Exception as e:
        rollbar.report_message(f'Unable to delete file path: {file_path}')

    return super().delete(record_id)
  
  def pack(self, rec):
    if rec is None:
      return {}

    if type(rec) is self._model_class:
      json = rec.to_json()
      if self.expanded('tags') and self.supports_tags():
        json['expand'] = {}
        tags = ContentCategoryMediaAssetRestBehavior().get_categories_by_asset(rec.id).all()
        json['expand']['tags'] = [tag.to_json() for tag in tags]

      return json
    else:
      return {self.underscore_to_camel(key):value for(key,value) in rec._asdict().items()}
    
  def update_user_tags(self, data, asset_id):
    if not data or not isinstance(data, dict) or not 'tags' in data or not self.supports_tags():
      return data
  
    return ContentCategoryMediaAssetRestBehavior(data=data).update_asset_tags(asset_id)  
