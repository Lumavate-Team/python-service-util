from ...models import VideoCategoryModel
from ..filetype_category_rest import FileTypeCategoryRestBehavior

class VideoFileTypeCategoryRestBehavior(FileTypeCategoryRestBehavior):
  def __init__(self, model_class=VideoCategoryModel, data=None, category_type='filetype'):
    super().__init__(model_class, data, category_type)