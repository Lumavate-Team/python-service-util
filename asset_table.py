from flask import request
from .base_asset import create_file_asset_model, create_category_model, create_asset_category_model
class AssetTable():
  def __init__(
    self,
    asset_model_class,
    category_model_class,
    asset_category_model_class
  ):
    self.asset_model_class=asset_model_class
    self.category_model_class=category_model_class
    self.asset_category_model_class=asset_category_model_class