from flask import request, g, make_response, abort
import urllib.parse
import uuid
import util
from ..aws import AwsClient
from lumavate_exceptions import ValidationException

class FileBehavior(object):
  def __init__(self):
    self.__client = AwsClient()

  def get_ephemeral_token(self):
    content_type = request.args.get("contentType", None)
    if content_type is None:
      raise ValidationException("contentType must be specified")

    key = self.get_temp_file_path()

    return self.__client.generate_presigned_post(key,
      conditions=[{'Content-Type': urllib.parse.unquote(content_type)}])

  def get_ephemeral_content(self, ephemeral_key, gzipped=False):
    if gzipped:
      return self.__client.objects.read_gzipped(path=ephemeral_key)

    return self.__client.objects.read(path=ephemeral_key)

  def get_ephemeral_thumbnail(self, key):
    try:
      obj = self.__client.objects.get(key)

      response = make_response(self.__client.objects.read(s3_object=obj))
      response.headers['Content-Type'] = obj.get('ContentType')

      return response

    except Exception as e:
      print(e, flush=True)
      abort(404)

  def delete(self, full_path):
    if full_path is not None:
      self.__client.delete_object(full_path)

  def get_temp_file_path(self, generate_file_name=False):
    result = '{company_id}/temp/{unique_id}__${{filename}}'.format(
      company_id=g.user["company"]["id"],
      unique_id=uuid.uuid4().hex)

    if generate_file_name:
      result = result.replace('${filename}', self.__client.objects.generate_unique_key())

    return result

  def get_full_path(self, path=None, file_name=None):
    if file_name is None:
      file_name = self.__client.objects.generate_unique_key()

    full_path = file_name
    if path is not None:
      full_path = '{}/{}'.format(path, file_name)

    return full_path

  def upload_file(self, file_content, content_type, destination_path=None, destination_file_name=None, temporary=False):
    metadata = {}
    full_path = self.get_full_path(destination_path, destination_file_name)
    if temporary:
      metadata['temporary'] = 'true'
      full_path = self.get_temp_file_path(generate_file_name=True if destination_file_name == None else False)
      if destination_file_name is not None:
        full_path = full_path.replace('${filename}', destination_file_name)

    self.__client.objects.write(
      full_path,
      file_content,
      content_type=content_type,
      metadata=metadata)

    return full_path

  def upload_ephemeral_file(self, path=None, file_name=None):
    data = request.get_json()
    ephemeral_key = data.get('ephemeralKey')
    if file_name is None:
      file_name = self.__client.objects.generate_unique_key()

    full_path = file_name
    if path is not None:
      full_path = '{}/{}'.format(path, file_name)

    obj = self.__client.objects.get(ephemeral_key)

    # Raw
    self.__client.objects.write(
      full_path,
      self.__client.objects.read_bytes(s3_object=obj),
      content_type=obj.get('ContentType'))

    return {
      'key': full_path
    }

  # copied from luthor but we might want to change this for service images
  def upload_ephemeral_content(self, data=None):
    if data is None:
      data = request.get_json()

    ephemeral_key = data.get('ephemeralKey')
    unique_key = self.__client.objects.generate_unique_key()
    obj = self.__client.objects.get(ephemeral_key)

    # Raw
    self.__client.objects.write(
      self.__client.objects.build_content_path(unique_key),
      self.__client.objects.read_bytes(s3_object=obj),
      content_type=obj.get('ContentType'))

    # Thumbnails
    self.__client.imaging.thumbnail(ephemeral_key, unique_key, [ 's', 'm', 'l' ])

    return {
      'key': unique_key,
      'preview': '/iot/files/{}'.format(unique_key),
      'previewLarge': '/iot/files/thumbs/L/{}'.format(unique_key),
      'previewMedium': '/iot/files/thumbs/M/{}'.format(unique_key),
      'previewSmall': '/iot/files/thumbs/S/{}'.format(unique_key)
    }

  def generate_presigned_url(self, key, expires_in=600):
    return self.__client.generate_presigned_url(key, expires_in)
