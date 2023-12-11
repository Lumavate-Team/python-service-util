from ...rest import RestBehavior
from ..content_paging import ContentPaging
from ...asset_table import AssetTable
from flask import request
from ..models import AudioAssetModel, DocumentAssetModel, ImageAssetModel, VideoAssetModel
from ..models import AudioCategoryModel, DocumentCategoryModel, ImageCategoryModel, VideoCategoryModel
from ..models import AudioAssetAudioCategoryModel, DocumentAssetDocumentCategoryModel, ImageAssetImageCategoryModel, VideoAssetVideoCategoryModel
from ...name_sort import NameSort
from ..content_column_select import ContentColumnSelect
from ..file_filter import FileFilter
import sys

class ContentCategoryRestBehavior(RestBehavior):
  def __init__(self, data=None, category_type=''):
    self._category_type = category_type
    self._asset_tables = self.getAssetTables()
    super().__init__(data)

  def apply_filter(self, q, model_class, ignore_fields=None):
    return FileFilter(self.args, ignore_fields, model_class).apply(q)

  def apply_sort(self, q):
    return NameSort().apply(q)

  def apply_select(self, q, model_class, asset_type):
    return ContentColumnSelect(model_class=model_class, asset_type=asset_type, args=self.get_args()).apply(q)

  def get_collection_query(self, asset_table):
    if asset_table is None:
      return None

    q = None
    if not self._category_type:
      q = asset_table.category_model_class.get_all()
    else:
      q = asset_table.category_model_class.get_all_by_type(self._category_type)

    q = self.apply_filter(q, asset_table.asset_category_model_class, ['org_id'])
    q = self.apply_sort(q)
    q = self.apply_select(q, asset_table.category_model_class, asset_table.asset_type)
    return q

  def get_collection(self):
    queries = []
    for asset_table in self._asset_tables:
      queries.append(self.get_collection_query(asset_table))

    q = queries.pop(0)

    if len(queries) > 0:
      q = q.union(*queries)

    return ContentPaging().run(q)
  
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
          asset_model_class=getattr(sys.modules[__name__], assetType.capitalize() + 'AssetModel'),
          category_model_class=getattr(sys.modules[__name__], assetType.capitalize() + 'CategoryModel'),
          asset_category_model_class=getattr(sys.modules[__name__], assetType.capitalize() + 'Asset' + assetType.capitalize() + 'CategoryModel'),
          asset_type=assetType
        )
      )

    return assetTables
  
  def pack(self, rec):
    if rec is None:
      return {}

    return rec.to_json()