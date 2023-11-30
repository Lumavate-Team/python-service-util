from ...models import DocumentAssetDocumentCategoryModel
from ..asset_tag_rest import AssetTagRestBehavior

class DocumentAssetTagRestBehavior(AssetTagRestBehavior):
  def __init__(self, model_class=DocumentAssetDocumentCategoryModel, data=None):
    super().__init__(model_class, data, 'tag')