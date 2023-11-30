from ...models import ImageCategoryModel
from ..filetype_category_rest import FileTypeCategoryRestBehavior

class ImageFileTypeCategoryRestBehavior(FileTypeCategoryRestBehavior):
  def __init__(self, model_class=ImageCategoryModel, data=None, category_type='filetype'):
    super().__init__(model_class, data, category_type)