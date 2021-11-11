import io
import json
import gzip
import uuid
from ..util import org_hash

class AwsObject(object):
  def __init__(self, client):
    self.__client = client

  def build_content_path(self, filename=None):
    return '{}content/{}/{}'.format(
        self.__client.default_bucket_prefix(),
        org_hash(g.org_id),
        filename if filename is not None else self.generate_unique_key)

  def build_temp_content_path(self, filename=None):
    return '{}content/{}/temp/{}'.format(
        self.__client.default_bucket_prefix(),
        org_hash(g.org_id),
        filename if filename is not None else self.generate_unique_key)

  def get(self, path):
    return self.__client.s3_bucket.Object(path).get()

  def generate_unique_key(self):
    return str(uuid.uuid4())[:8]

  def raw_stream(self, path=None, s3_object=None):
    if path is None and s3_object is None:
      raise ValueError('Missing S3 object or key path')

    s3_object = s3_object or self.get(path)

    return s3_object['Body']._raw_stream

  def read(self, path=None, s3_object=None):
    if path is None and s3_object is None:
      raise ValueError('Missing S3 object or key path')

    s3_object = s3_object or self.get(path)

    return s3_object['Body'].read(s3_object['ContentLength'])

  def read_bytes(self, path=None, s3_object=None):
    return io.BytesIO(self.read(path, s3_object))

  def read_text(self, path=None, s3_object=None):
    return self.read(path, s3_object).decode('utf-8')

  def read_json(self, path=None, s3_object=None):
    return json.loads(self.read_text(path, s3_object))

  def read_gzipped(self, path=None, s3_object=None):
    return gzip.decompress(self.read(path, s3_object))

  def filter_objects(self, prefix):
    paginator = self.__client.s3_resource.meta.client.get_paginator('list_objects')

    for page in paginator.paginate(Bucket=self.__client.default_bucket_name, Prefix=prefix):
      if 'Contents' in page:
        for obj in page['Contents']:
          yield obj

  def write(self, path, file_contents, content_type='text/plain', content_encoding='', cache_control=None, metadata=None, tagging=''):
    if metadata is None:
      metadata = {}

    new_file = self.__client.s3_bucket.Object(path)

    tags = f'org_id={g.org_id}'
    if tagging:
      tags = f'{tags}&{tagging}'

    if cache_control is None:
      new_file.put(
        Body=file_contents.read(),
        ContentType=content_type,
        ContentEncoding=content_encoding,
        Metadata=metadata,
        Tagging=tagging)
    else:
      max_age = 'max-age=' + str(cache_control)
      metadata['Cache-Control'] = max_age

      new_file.put(
        Body=file_contents,
        ContentType=content_type,
        ContentEncoding=content_encoding,
        Metadata=metadata,
        Tagging=tagging,
        CacheControl=max_age)

    new_file.Acl().put(ACL='public-read')

    return new_file

  def write_json(self, path, json_data):
    self.write(path,
      str.encode(json.dumps(json_data, cls=pyro.CustomEncoder)), content_type='application/json')

