class DataColumn():
  def __init__(self, column_id, name, display_name, type, is_active, options={}):
    self.id = column_id;
    self.name = name;
    self.display_name = display_name;
    self.column_type = type
    self.is_active = is_active
    self.options = options

  def to_json(self):
    return {
      'id': self.id,
      'name': self.name,
      'displayName': self.display_name,
      'columnType': {
        'value': self.type,
        'options': self.options
      },
      'isActive': self.is_active
    }

  @staticmethod
  def from_json(column):
    return DataColumn(
        column.get('id'),
        column.get('columnName'),
        column.get('columnDisplayName'),
        column.get('columnType',{}).get('value'),
        column.get('isActive'),
        options=column.get('columnType', {}).get('options', None))


