from flask import request
from .base_asset import create_file_asset_model, create_category_model, create_asset_category_model

def getAssetTables(self):
    assetTypes = request.args.get('assettypes')

    if assetTypes is None:
      raise Exception("assettypes is required")

    assetTypes = assetTypes.split('||')

    if not assetTypes:
      raise Exception("assettypes is required")

    if not set(assetTypes).issubset(['audio', 'document', 'image', 'video']):
      raise Exception("Invalid assettypes")

    assetTables = []

    for assetType in assetTypes:
      assetTables.append(
        AssetTable(
          asset_model_class=BaseAsset.create_file_asset_model(assetType + '_asset'),
          category_model_class=BaseAsset.create_category_model(assetType + '_category'),
          asset_category_model_class=BaseAsset.create_asset_category_model(
            assetType + '_asset_' + assetType + '_category',
            BaseAsset.create_category_model(assetType + '_category')
          )
        )
      )

    return assetTables

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