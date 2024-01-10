from enum import Enum

class ContentAssetTypes(str, Enum):
  AUDIO = 'audio',
  DOCUMENT = 'document',
  IMAGE = 'image',
  VIDEO = 'video'