from ...models import AudioCategoryModel
from ..filetype_category_rest import FileTypeCategoryRestBehavior

class AudioFileTypeCategoryRestBehavior(FileTypeCategoryRestBehavior):
  def __init__(self, model_class=AudioCategoryModel, data=None, category_type='filetype'):
    super().__init__(model_class, data, category_type)