from ..category_rest import CategoryRestBehavior
from ...models import AudioCategoryModel

class AudioCategoryRestBehavior(CategoryRestBehavior):
  def __init__(self, model_class=AudioCategoryModel, data=None, category_type=''):
    self._category_type = category_type
    super().__init__(model_class, data, category_type)