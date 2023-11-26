from ..models import ContentCategoryModel
from .static_category_rest import StaticCategoryRestBehavior

class FileTypeCategoryRestBehavior(StaticCategoryRestBehavior):
  def __init__(self, model_class=ContentCategoryModel, data=None):
    super().__init__(model_class, data, 'filetype')