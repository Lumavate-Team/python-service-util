from ...rest import RestBehavior
from ...paging import Paging
from ...asset_table import AssetTable
from flask import request
from ..models import create_file_asset_model, create_category_model, create_asset_category_model

class ContentCategoryRestBehavior(RestBehavior):
  def __init__(self, data=None, category_type=''):
    self._category_type = category_type
    self._asset_tables = self.getAssetTables()
    super().__init__(data)

  def get_collection_query(self, asset_table):
    if asset_table is None:
      return None

    q = None
    if not self._category_type:
      q = asset_table.category_model_class.get_all()
    else:
      q = asset_table.category_model_class.get_all_by_type(self._category_type)

    q = self.apply_filter(q, asset_table.asset_category_model_class)
    q = self.apply_sort(q)
    q = self.apply_select(q, asset_table.asset_category_model_class)
    return q

  def get_collection(self):
    queries = []
    for asset_table in self._asset_tables:
      queries.append(self.get_collection_query(asset_table))

    q = queries.pop(0)

    if len(queries) > 0:
      q = q.union(*queries)

    return Paging().run(q, self.pack)
  
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
          asset_model_class=create_file_asset_model(assetType + '_asset'),
          category_model_class=create_category_model(assetType + '_category'),
          asset_category_model_class=create_asset_category_model(
            assetType + '_asset_' + assetType + '_category',
            create_category_model(assetType + '_category')
          )
        )
      )

    return assetTables