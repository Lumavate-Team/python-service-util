from ...models import DocumentCategoryModel
from ..filetype_category_rest import FileTypeCategoryRestBehavior

class DocumentFileTypeCategoryRestBehavior(FileTypeCategoryRestBehavior):
  def __init__(self, model_class=DocumentCategoryModel, data=None, category_type='filetype'):
    super().__init__(model_class, data, category_type)