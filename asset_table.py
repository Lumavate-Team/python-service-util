from flask import request
class AssetTable():
  def __init__(
    self,
    asset_model_class,
    category_model_class,
    asset_category_model_class,
    asset_type
  ):
    self.asset_model_class=asset_model_class
    self.category_model_class=category_model_class
    self.asset_category_model_class=asset_category_model_class
    self.asset_type=asset_type