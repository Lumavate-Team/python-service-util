from ..category_rest import CategoryRestBehavior
from ...models import DocumentCategoryModel

class DocumentCategoryRestBehavior(CategoryRestBehavior):
  def __init__(self, model_class=DocumentCategoryModel, data=None, category_type=''):
    self._category_type = category_type
    print(self._category_type, flush=True)
    super().__init__(model_class, data, category_type)