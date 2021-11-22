from flask import request, g, make_response, abort
import urllib.parse
import uuid
from ..aws import AwsClient
from ..util import org_hash
from lumavate_exceptions import ValidationException, NotFoundException

class FileBehavior(object):
  def __init__(self):
    self.__client = AwsClient()

  # Used to generate a presigned post for client side file uploads
  # When a file is uploaded using this, it has a TempFile=True tag
  # which is tied to a lifecycle rule to delete the file after a day.
  # When property sheets or a form is saved, the TempFile tag is removed and the file becomes permanent.
  def generate_presigned_post(self):
    content_type = request.args.get("contentType", None)
    if content_type is None:
      raise ValidationException("contentType must be specified")

    key = self.__client.objects.build_content_path()
    tags = {
        'TempFile': 'True',
        'OrgId': g.org_id
        }
    tag_xml = ''
    for k,v in tags.items():
      tag_xml = f'{tag_xml}<Tag><Key>{k}</Key><Value>{v}</Value></Tag>'

    tagging_xml = f'<Tagging><TagSet>{tag_xml}</TagSet></Tagging>'
    fields = {
      'tagging': tagging_xml
        }

    conditions=[
        {'Content-Type': urllib.parse.unquote(content_type)},
        ['starts-with', '$tagging', tagging_xml]]

    return self.__client.generate_presigned_post(key,fields=fields, conditions=conditions)

  def generate_presigned_url(self, key, expires_in=600):
    return self.__client.generate_presigned_url(key, expires_in)

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

  def get_full_path(self, path=None, file_name=None):
    if file_name is None:
      file_name = self.__client.objects.generate_unique_key()

    full_path = file_name
    if path is not None:
      full_path = '{}/{}'.format(path, file_name)
    else:
      full_path = self.__client.objects.build_content_path(file_name)

    return full_path

  def upload_file(self, file_content, content_type, destination_path=None, destination_file_name=None, temporary=False):
    metadata = {}
    full_path = self.get_full_path(destination_path, destination_file_name)
    if temporary:
      metadata['temporary'] = 'true'
      full_path = self.__client.objects.build_temp_content_Path(destination_file_name)

    self.__client.objects.write(
      full_path,
      file_content,
      content_type=content_type,
      metadata=metadata)

    return full_path

  # update_file_tags overrides existing object tags
  # This is used to effectively remove the TempFile tag set on initial upload(before save)
  # and make the file permanent.
  # If you need additional tags, it needs to be a list of dictionaries of Key/Value pairs
  # tagging = [{'Key': <tag name>, 'Value': <value of tag, must be string>},...]
  #
  # OrgId tag is included already
  def update_file_tags(self, object_key, tagging=[]):
    obj = self.__client.objects.get(object_key)

    tags = [{ 'Key': 'OrgId', 'Value': str(g.org_id)}]
    for tag in tagging:
      tags.append(tag)

    self.__client.put_object_tags(object_key, tags=tags)

  def get_file(self, file_path):
    hashed_jwt_org = org_hash(g.org_id)
    file_path_split = file_path.split('/')

    # get the hashed org_id from the s3 file_path which is 2nd to last index
    hashed_path_org = file_path_split[len(file_path_split)-2]

    # validate jwt owner and file path are for same org
    if hashed_jwt_org != hashed_path_org:
      raise NotFoundException('Invalid file path')

    obj = self.__client.objects.get(file_path)

    response = make_response(self.__client.objects.read(s3_object=obj))
    response.headers['Content-Type'] = obj.get('ContentType')
    response.cache_control.max_age = 1209600
    return response

  def upload_ephemeral_file(self, ephemeral_key, path=None, file_name=None, tagging=None):
    if file_name is None:
      file_name = self.__client.objects.generate_unique_key()

    full_path = file_name
    if path is not None:
      full_path = '{}/{}'.format(path, file_name)
    else:
      full_path = self.__client.objects.build_content_path(file_name)

    obj = self.__client.objects.get(ephemeral_key)

    # Raw
    self.__client.objects.write(
      full_path,
      self.__client.objects.read_bytes(s3_object=obj),
      content_type=obj.get('ContentType'),
      tagging=tagging)

    return {
      'key': full_path
    }

  def upload_ephemeral_content(self, ephemeral_key, tagging=None):
    unique_key = self.__client.objects.generate_unique_key()
    obj = self.__client.objects.get(ephemeral_key)

    # Raw
    self.__client.objects.write(
      self.__client.objects.build_content_path(unique_key),
      self.__client.objects.read_bytes(s3_object=obj),
      content_type=obj.get('ContentType'),
      tagging=tagging)

    # Thumbnails
    self.__client.imaging.thumbnail(ephemeral_key, unique_key, [ 's', 'm', 'l' ])

    return {
      'key': unique_key,
      'preview': '/iot/files/{}'.format(unique_key),
      'previewLarge': '/iot/files/thumbs/L/{}'.format(unique_key),
      'previewMedium': '/iot/files/thumbs/M/{}'.format(unique_key),
      'previewSmall': '/iot/files/thumbs/S/{}'.format(unique_key)
    }

