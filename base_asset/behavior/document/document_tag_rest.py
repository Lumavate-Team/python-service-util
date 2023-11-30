from ..tag_rest import TagRestBehavior
from ...models import DocumentCategoryModel
from .document_category_rest import DocumentCategoryRestBehavior
from lumavate_exceptions import ValidationException

class DocumentTagRestBehavior(TagRestBehavior):
  def __init__(self, model_class=DocumentCategoryModel, data=None):
    super().__init__(model_class, data, 'tag')

  def batch_tags(self):
    data = self.get_data().get('data', [])
    response = []

    self.batch_validate_names(data)

    for tag in data:
      operation = tag.get('operation', '')
      if not operation:
        continue

      tag['type'] = 'tag'
      handler = DocumentCategoryRestBehavior(data=tag, category_type='tag')
      if tag['name'].lower() in self.banned_tags():
        raise ValidationException("Invalid tag name", api_field='name')

      if operation == 'add':
        response.append(handler.post())
      if operation == 'modify':
        response.append(handler.put(tag['id']))
      if operation == 'delete':
        response.append(handler.delete(tag['id']))

    return response