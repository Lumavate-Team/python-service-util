from ..category_rest import CategoryRestBehavior
from ...models import VideoCategoryModel

class VideoCategoryRestBehavior(CategoryRestBehavior):
  def __init__(self, model_class=VideoCategoryModel, data=None, category_type=''):
    self._category_type = category_type
    super().__init__(model_class, data, category_type)