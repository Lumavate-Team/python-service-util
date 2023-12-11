from ..column_select import ColumnSelect
from sqlalchemy import literal
from app import db

class ContentColumnSelect(ColumnSelect):
  def __init__(self, model_class, asset_type, args=None):
    self._asset_type = asset_type
    super().__init__(model_class, args)

  def apply(self, base_query):
    column_list = self.get_column_list()
    return base_query.with_entities(*column_list, literal(self._asset_type).label("asset_type"))
