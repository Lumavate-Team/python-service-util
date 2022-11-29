from enum import Enum

class ColumnDataType(str, Enum):
  BOOLEAN = 'boolean'
  DATETIME = 'datetime'
  DROPDOWN = 'dropdown'
  NUMERIC = 'numeric'
  TEXT = 'text'
  FILE = 'file'
  RICHTEXT = 'richtext'
  DOCUMENT = 'document'
  IMAGE = 'image'
  VIDEO = 'video'
