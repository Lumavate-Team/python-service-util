from app import db
from flask import g
from sqlalchemy import select, delete, and_, or_, cast, union, Text, case
from sqlalchemy.sql import expression
from sqlalchemy.orm import validates
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.functions import coalesce
from hashids import Hashids
from lumavate_exceptions import ValidationException
from ...db import BaseModel, Column
from ...aws import FileBehavior
from ..column import DataColumn
from ..models.asset_model import AssetBaseModel
from json import loads
from dateutil.parser import *
from dateutil.tz import *
from datetime import *
from time import time, sleep
import pytz
import re

class AbstractDataAssetModel(BaseModel):
  __abstract__ = True

  org_id = Column(db.BigInteger, nullable=False, createable=True, updateable=False, viewable=False)
  submitted_data = Column(JSONB, server_default='{}', nullable=True)
  activation_code = Column(db.String(35), nullable=True)
  created_by = Column(db.String(255), nullable=False)
  last_modified_by = Column(db.String(255), nullable=False)
  is_draft = Column(db.Boolean, server_default=expression.false(), nullable=True)
  public_id = Column(db.String(200), nullable=False)

  @classmethod
  def get_type_model(cls):
    pass
  
  @classmethod
  def get_related_products_model(cls):
    pass

  @classmethod
  def get_all(cls, args=None):
    return cls.query.filter_by(org_id=g.org_id)

  @classmethod
  def get(cls, id):
    return cls.get_all().filter_by(id=id).first()
  
  @classmethod
  def get_all_by_asset_id(cls, asset_id, args=None):
    query = cls.get_all(args).filter_by(type_id=asset_id)

    if 'draft' in args:
      # python bool cast of a string returns True no matter value if its not empty
      # must compare against string
      draft = args.get('draft') == 'True'
    else:
      draft = True

    exclude_draft = draft == False
    if exclude_draft:
      query = query.filter(or_(cls.is_draft == None,cls.is_draft==False))

    return query

  @classmethod
  def get_all_by_asset_id_activation(cls, asset_id):
    if g.token_data.get('code', None):
      return cls.get_all().filter_by(type_id=asset_id,activation_code=g.token_data.get('code', None))

    return []

  @classmethod
  def get_by_public_id(cls, asset_id, public_id):
    return cls.get_all().filter_by(type_id=asset_id, public_id=public_id).first()

  @validates('submitted_data')
  def validate_data(self, key, data):
    if not data:
      return data

    if type(data) == str:
      data.replace("'", '"')
      data = loads(data)

    schema_columns = self.get_column_definitions(self.type_id if self.type_id else self.asset_id)
    column_dict = {column_def.get('columnName'): DataColumn.from_json(column_def) for column_def in schema_columns}
    time_patterns = self.get_compiled_time_patterns()
    tzinfo_dict = dict(self.gen_tzinfos())

    for data_key, value in data.items():
      column = column_dict.get(data_key.lower())
      if column is None:
        # not all submitted values are tied to the columns, some are asset related, just skip them
        continue

      if column.column_type == 'text':
        if type(value) != str:
          raise ValidationException('Field must be text', column.name)

      elif column.column_type == 'numeric':
        if value in ["", None]:
          continue
        try:
          data[data_key] = float(value)
        except:
          raise ValidationException('Field must be numeric', column.name)

      elif column.column_type == 'dropdown':
        continue

      elif column.column_type == 'boolean':
        if value not in [True, False, 'true', 'false', 'True', 'False', 'TRUE', 'FALSE', '']:
          raise ValidationException('Field must be valid boolean', column.name)
        if value in ['true', 'True', 'TRUE', True]:
          data[data_key] = True
        elif value in ['false', 'False', 'FALSE', False]:
          data[data_key] = False

      if column.column_type == 'datetime':
        data[data_key] = self.validate_datetime(value, column.name, time_patterns, tzinfo_dict)

    return data

  @validates('asset_id')
  def validate_asset_id(self, key, value):
    if value is not None:
      if AssetBaseModel().get(value) is None:
        raise ValidationException('Invalid asset id', key)
      return value
    
  def before_insert(self):
    self.set_public_id()
    super().before_insert()

  def validate_datetime(self, value, column_name, time_patterns=[], tzinfo_dict={}):
    if not value:
      return None

    value = value.strip()
    try:
      if self.is_time_only(value, time_patterns):
        return parse(value).strftime("0001-01-01 %H:%M:%S")
      else:
        dt = parse(value, tzinfos=tzinfo_dict)
        if dt.tzinfo:
          return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")
        else:
          return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ParserError as e:
      raise ValidationException(f'Invalid datetime value: {value} for column {column_name}', column_name)
    except UnknownTimezoneWarning as e:
      raise ValidationException(f'Unknown timezone in value: {value} for column {column_name}', column_name)

  def is_time_only(self, value, time_patterns):
    for pattern in time_patterns:
      match = pattern.match(str(value))
      if bool(match):
        return True

    return False

  def get_compiled_time_patterns(self):
    # patterns to compile for reuse
    #HH:MM 12-hour, optional leading 0 and optional seconds am/pm,
    #HH:MM 24-hour, optional leading 0 and optional seconds
    time_formats = [
      "^(0?[1-9]|1[0-2])(:[0-5][0-9])(:[0-5][0-9])? ?([AaPp][Mm])$",
      "^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$"
    ]

    return [re.compile(pattern) for pattern in time_formats]

  # From https://www.py4u.net/discuss/11495 on how to get timezone mappings
  def gen_tzinfos(self):
    for zone in pytz.common_timezones:
      try:
        tzdate = pytz.timezone(zone).localize(datetime.utcnow(), is_dst=None)
      except pytz.NonExistentTimeError:
        pass
      else:
        tzinfo = gettz(zone)

        if tzinfo:
          yield tzdate.tzname(), tzinfo

  #TODO: consolidate with table builder into service util
  @classmethod
  def get_file_paths(cls, data_rows, file_columns):
    file_paths = []
    if not file_columns or len(file_columns) == 0:
      return file_paths

    submitted_data = (
      select([cls.submitted_data]) 
      .select_from(cls)
      .where(cls.id.in_(data_rows)))
    results = [dict(row) for row in db.session.execute(submitted_data)]

    for row_result in results:
      row = row_result['submitted_data']
      for column in file_columns:
        if column in row and isinstance(row[column],dict) and row[column].get('s3FilePath'):
          file_paths.append(row[column]['s3FilePath'])
    
    return file_paths

  #TODO: consolidate with table builer into service util
  def set_public_id(self):
    #imports are too fast
    sleep(0.01)
    # get a timestamp to make hash unique since there is no id yet.
    timestamp = int(time() * 1000)
    self.public_id = 'p{}'.format(Hashids(min_length=8,
        salt='T2uDF0uSWF8RwU6IdL0x',
        alphabet='abcdefghijklmnopqrstuvwxyz1234567890').encode(timestamp))
    
  #TODO: consolidate with table builder into service util  DataBaseModel
  @classmethod
  def delete_data_chunk(cls, asset_id, file_columns, chunk_size=1000):
    data_rows = (
      select([cls.id])
      .select_from(cls)
      .where(and_(
        cls.org_id == g.org_id,
        cls.type_id == asset_id))
      .limit(chunk_size)
      .alias('data_rows'))

    file_paths = cls.get_file_paths(data_rows, file_columns)
    s3_response = FileBehavior().delete_objects(file_paths)

    delete_query = (delete(cls)
      .where(cls.id.in_(data_rows))
      .returning(cls.id))
    
    results = db.session.execute(delete_query)

    return  [dict(row) for row in results]

  def to_json(self):
    submitted_data = self.submitted_data

    # push custom columns onto flat submitted_data dictionary when coming from app
    # to keep component behavior the same across data assets
    if g.get('token_data',{}).get('scope','') == 'runtime':
      submitted_data = {key:value for key,value in self.submitted_data.items() if key != 'columns'}
      for column,value in self.submitted_data.get('columns',{}).items():
        submitted_data[column] = value
    
    response = {
      'id': self.public_id,
      'assetId': self.type_id,
      'activationCode': self.activation_code,
      'createdBy': self.created_by,
      'createdAt': self.created_at,
      'lastModifiedBy': self.last_modified_by,
      'lastModifiedAt': self.last_modified_at,
      'isDraft': self.is_draft,
      'submittedData': submitted_data
    }

    return response
  
  @classmethod
  def get_all_overview(cls, asset_id, args=None):
    asset = cls.get_type_model()
    column_cte = select([
        asset.id,
        cast(asset.data.op('->')('headlineField').op('->>')('columnName'), Text).label('headlineField'), 
        case([(asset.data.op('->')('headlineField').op('->>')('id') == None, True)], else_=False).label('isHeadlineBase'), 
        coalesce(cast(asset.data.op('->')('subheadlineField').op('->>')('columnName'), Text), 'sku').label('subheadlineField'),
        case([(asset.data.op('->')('subheadlineField').op('->>')('id') == None, True)], else_=False).label('isSubheadlineBase')])\
      .select_from(asset)\
      .where(and_(asset.org_id == g.org_id, asset.id == asset_id)) \
      .cte('asset_columns')

    return db.session.query(
        cast(cls.submitted_data.op('->>')('eventName'), Text).label('event_name'),
        case([
          (column_cte.c.isHeadlineBase == True, 
            coalesce(cast(cls.submitted_data.op('->>')(column_cte.c.headlineField), Text),''))],
          else_ = 
            coalesce(cast(cls.submitted_data.op('->')('columns').op('->>')(column_cte.c.headlineField),Text),''))\
        .label('headline_field'),
        case([
          (column_cte.c.subheadlineField == None, 
            None),
          (column_cte.c.isSubheadlineBase == True,
            coalesce(cast(cls.submitted_data.op('->>')(column_cte.c.subheadlineField), Text), None))],
          else_ =
            coalesce(cast(cls.submitted_data.op('->')('columns').op('->>')(column_cte.c.subheadlineField), Text), ''))\
        .label('subheadline_field'),
        cls.public_id,
        cls.type_id
        )\
        .select_from(cls)\
        .join(column_cte, cls.org_id == g.org_id)

  @classmethod
  def get_column_definitions(cls, asset_id):
    return cls.get_type_model().get_column_definitions(asset_id)

  @classmethod
  def get_related_product_ids(cls, data_id):
    r = cls.get_related_products_model()

    event_query = select([r.parent_id])\
      .select_from(r)\
      .where(and_(r.child_id == data_id, r.org_id == g.org_id))

    product_query = select([r.child_id])\
      .select_from(r)\
      .where(and_(r.parent_id == data_id, r.org_id == g.org_id))

    return union(event_query, product_query)

  @classmethod
  def delete_org(cls, org_id):
    return cls.query.filter_by(org_id=org_id).delete()