from enum import Enum

class AssetSelectorMode(str, Enum):
  READ = 'read',
  WRITE = 'write',
  BOTH = 'both'

