from enum import Enum

class ColumnDataType(str, Enum):
  BOOLEAN = 'boolean'
  DATETIME = 'datetime'
  DROPDOWN = 'dropdown'
  NUMERIC = 'numeric'
  TEXT = 'text'
