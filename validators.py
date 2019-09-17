from lumavate_exceptions import ValidationException
from dateutil.parser import parse
from enum import EnumMeta
from flask import g
import datetime
import re

class BaseValidator:
  def __init__(self, propertyName, allow_none=True):
    self.propertyName = propertyName
    self.allow_none = allow_none

  def validate(self, value):
    if not self.allow_none and not value:
      message = "Expected value"
      raise ValidationException(message, api_field=self.propertyName)

    return value

class BooleanValidator(BaseValidator):
  def __init__(self, propertyName, allow_none=True):
    super().__init__(propertyName, allow_none=allow_none)

  def validate(self, value):
    if value:
      return str(value).lower() == 'true'
    else:
      return False

class ArrayValidator(BaseValidator):
  def __init__(self, propertyName, allow_none=True, item_validator=None):
    super().__init__(propertyName, allow_none=allow_none)
    self.item_validator = item_validator

  def validate(self, value):
    value = super().validate(value)
    if value:
      if not isinstance(value, list):
        message = "Expected array value"
        raise ValidationException(message, api_field=self.propertyName)

      if self.item_validator:
        value = [self.item_validator(sv) for sv in value]

    return value

class IntValidator(BaseValidator):
  def __init__(self, propertyName, allow_none=True, max=None, min=None):
    self.max = max
    self.min = min
    super().__init__(propertyName, allow_none)

  def validate(self, value):
    if not self.allow_none and value is None:
      message = "Expected value"
      raise ValidationException(message, api_field=self.propertyName)

    if value is not None:
      if str(value).isdigit():
        value = int(str(value))

      if not isinstance(value, int):
        message = "Expected int value"
        raise ValidationException(message, api_field=self.propertyName)

      if self.max is not None:
        if value > self.max:
          message = "Value out of range (max value allowed is {})".format(self.max)
          raise ValidationException(message, api_field=self.propertyName)

      if self.min is not None:
        if value < self.min:
          message = "Value out of range (min value allowed is {})".format(self.min)
          raise ValidationException(message, api_field=self.propertyName)

    return value

class EnumValidator(BaseValidator):
  def __init__(self, propertyName, allowed_values, allow_none=True):
    if isinstance(allowed_values, EnumMeta):
      self.allowed_values = []
      for x in allowed_values:
        self.allowed_values.append(x.value)
    else:
      self.allowed_values = allowed_values

    super().__init__(propertyName, allow_none=allow_none)

  def validate(self, value):
    if value is not None:
      value = str(value)

    value = super().validate(value)
    if value:
      if not value in self.allowed_values:
        message = "Expected values ({})".format(self.allowed_values)
        raise ValidationException(message, api_field=self.propertyName)

    return value

class StringValidator(BaseValidator):
  def __init__(self, propertyName, allow_none=True, max_length=None):
    self.max_length = max_length
    super().__init__(propertyName, allow_none=allow_none)

  def validate(self, value):
    value = super().validate(value)
    if value is not None:
      if not self.allow_none and value == '':
        raise ValidationException(
            'Expected value', api_field=self.propertyName)

      if not isinstance(value, str):
        message = "Expected string value"
        raise ValidationException(message, api_field=self.propertyName)

      if self.max_length is not None and len(value) > self.max_length:
        message = "Max length of {} exceeded".format(self.max_length)
        raise ValidationException(message, api_field=self.propertyName)

    return value

class UrlValidator(StringValidator):
  def __init__(self, propertyName, allow_none=True):
    super().__init__(propertyName, allow_none=allow_none)

  def validate(self, value):
    value = super().validate(value)
    if value:
      regex = re.compile(
          '^(http|https)?://([^/:]+\.[a-z]{2,10}|([0-9]{{1,3}}\.){{3}}[0-9]{{1,3}})(:[0-9]+)?(\/.*)?$', re.IGNORECASE)
      if regex.fullmatch(value):
        return value

      message = "Expected url value"
      raise ValidationException(message, api_field=self.propertyName)

    return value


class FloatValidator(BaseValidator):
  def __init__(self, propertyName, allow_none=True):
    super().__init__(propertyName, allow_none=allow_none)

  def validate(self, value):
    if not self.allow_none and value is None:
      message = 'Expected value'
      raise ValidationException(message, api_field=self.propertyName)

    if value is not None:
      try:
        value = float(str(value))
      except:
        message = 'Expected float value'
        raise ValidationException(message, api_field=self.propertyName)

      if not isinstance(value, float) and not isinstance(value, int):
        message = 'Expected float value'
        raise ValidationException(message, api_field=self.propertyName)

    return value

class DictionaryValidator(BaseValidator):
  def __init__(self, propertyName, allow_none=True, validator=None):
    self.validator = validator
    super().__init__(propertyName, allow_none)

  def validate(self, value):
    value = super().validate(value)
    if value:
      if not isinstance(value, dict):
        message = "Expected dictionary value"
        raise ValidationException(message, api_field=self.propertyName)

      if self.validator:
        value = self.validator(value)

    return value

class DateTimeValidator(BaseValidator):
  def __init__(self, propertyName, allow_none=True):
    super().__init__(propertyName, allow_none=allow_none)

  def validate(self, value):
    if not self.allow_none and value is None:
      message = "Expected value"
      raise ValidationException(message, api_field=self.propertyName)

    if value is not None:
      if isinstance(value, datetime.date):
        return value

      if hasattr(value, 'isoformat'):
        value = value.isoformat()
      else:
        value = str(value)

      try:
        value = parse(value)
      except Exception as e:
        print(e, flush=True)
        message = "Expected Datetime format"
        raise ValidationException(message, api_field=self.propertyName)

    return value