from sqlalchemy import func
from app import db
from ..models import ContentCategoryModel
from .category_rest import CategoryRestBehavior
from lumavate_exceptions import NotFoundException, ValidationException, InvalidOperationException

class ContentCategoryRestBehavior(CategoryRestBehavior):
  def __init__(self, model_class=ContentCategoryModel, data=None):
    super().__init__(model_class, data, 'tag')

  def banned_tags(self):
    return ['undefined', 'none', 'true', 'false', 'null', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'bmp', 'csv', 'exe', 'jpg', 'jpeg', 'mov', 'mp3', 'mp4', 'png', 'tif', 'tiff', 'tmp', 'txt', 'zip', 'svg', 'gif']

  def validate_tag_name(self, property_data, record_id=None):
    if 'name' not in property_data:
      return

    existing_tags = self._model_class.get_all_by_type('tag') \
        .filter(func.lower(self._model_class.name) == func.lower(property_data.get('name'))).first()

    if existing_tags is not None and (record_id is None or existing_tags.id != record_id):
      name = property_data.get('name')
      raise ValidationException(f'Tag name: {name} is already in use.', 'name')

  def batch_validate_names(self, data):
    new_data = [tag for tag in data if tag.get('operation', '') and tag.get('operation') != 'delete']
    names = [tag['name'].lower() for tag in new_data]
    existing_tags = self._model_class.get_all_by_type('tag') \
        .filter(func.lower(self._model_class.name).in_(names))

    for tag in existing_tags:
      found = False
      for current_tag in new_data:
        if tag.id == current_tag.get('id', ''):
          found = True
          break
      if not found:
        name = tag.name
        raise ValidationException(f'Tag name: {name} is already in use.', 'name')

  def batch_tags(self):
    data = self.get_data().get('data', [])
    response = []

    self.batch_validate_names(data)

    for tag in data:
      operation = tag.get('operation', '')
      if not operation:
        continue

      tag['type'] = 'tag'
      
      if operation == 'add':
        lastCategory = self._model_class.get_last_by_old_id()
        tag['containerId'] = self._model_class._get_current_container()
        tag['oldId'] = 1 if lastCategory == None else lastCategory.old_id+1

      handler = CategoryRestBehavior(model_class=ContentCategoryModel, data=tag, category_type='tag')
      if tag['name'].lower() in self.banned_tags():
        raise ValidationException("Invalid tag name", api_field='name')
      
      if operation == 'add':
        response.append(handler.post())
      if operation == 'modify':
        response.append(handler.put(tag['oldId']))
      if operation == 'delete':
        response.append(handler.delete(tag['oldId']))

    return response
  
  def get_asset_tags(self, asset_id):
    return self._model_class.get_by_asset_id(asset_id)