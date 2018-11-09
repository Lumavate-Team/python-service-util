from datetime import datetime, date
import decimal
import json
import uuid

class CustomEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, datetime) or isinstance(obj, date):
      return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
      return float(obj)
    elif isinstance(obj, uuid.UUID):
      return str(obj)
    elif callable(obj):
      return obj()

    return json.JSONEncoder.default(self, obj)
