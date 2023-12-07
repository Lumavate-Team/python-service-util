from .content_category_rest_behavior import ContentCategoryRestBehavior

class ContentTagRestBehavior(ContentCategoryRestBehavior):
  def __init__(self, data=None, category_type='tag'):
    self._category_type = category_type
    super().__init__(data, category_type)