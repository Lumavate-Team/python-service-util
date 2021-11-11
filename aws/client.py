from flask import current_app
import boto3
import botocore
import os
from .objects import AwsObject

class AwsClient(object):
  def __init__(self):
    self.__s3_client = None
    self.__s3_resource = None
    self.__s3_bucket = None

    self.__objects = AwsObject(self)

  @property
  def default_region_name(self):
    return os.environ.get('AWS_REGION')

  @property
  def default_bucket_name(self):
    return os.environ.get('S3_BUCKET')

  @property
  def default_bucket_prefix(self):
    prefix = os.environ.get('S3_BUCKET_PREFIX','')
    if prefix:
      return f'{prefix.strip("/")}/'

    return ''

  @property
  def objects(self):
    return self.__objects

  @property
  def s3_client(self):
    if self.__s3_client is None:
      self.__s3_client = boto3.client('s3',
      aws_access_key_id= os.environ.get('AWS_ACCESS_KEY_ID'),
      aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    return self.__s3_client

  @property
  def s3_resource(self):
    if self.__s3_resource is None:
      self.__s3_resource = boto3.resource('s3', region_name=self.default_region_name)

    return self.__s3_resource

  @property
  def s3_bucket(self):
    if self.__s3_bucket is None:
      self.__s3_bucket = self.s3_resource.Bucket(self.default_bucket_name)

    return self.__s3_bucket

  def delete_objects_with_prefix(self, prefix):
    response = self.s3_client.list_objects(
      Bucket=self.default_bucket_name,
      Prefix=prefix)

    # If no contents or empty contents, get out
    if not response.get('Contents'):
      return

    matching_keys = [{'Key': k} for k in [obj.get('Key') for obj in response.get('Contents')]]
    return self.s3_bucket.delete_objects(
      Bucket=self.default_bucket_name,
      Delete={'Objects': matching_keys})

  def delete_object(self, key):
    return self.s3_client.delete_object(
        Bucket=self.default_bucket_name,
        Key=key)

  def generate_presigned_url(self, key, expires_in=600):
    return self.s3_client.generate_presigned_url(
      'get_object',
      Params= {'Bucket': self.default_bucket_name, 'Key': key },
      ExpiresIn=expires_in)

  def generate_presigned_post(self, key, expires_in=600, conditions=None):
    return self.s3_client.generate_presigned_post(
      self.default_bucket_name,
      key,
      ExpiresIn=expires_in,
      Conditions=conditions)

  # Returns existing or an empty config if one doesn't exist. It does not create though.
  def get_lifecycle_config(self):
    try:
      return self.s3_client.get_bucket_lifecycle_configuration(Bucket=self.default_bucket_name)
    except botocore.exceptions.ClientError as e:
      code = e.response.get('Error',{}).get('Code','')
      if code == 'NoSuchLifecycleConfiguration':
        return { 'Rules': []}
      else:
        raise
    except Exception as e:
      raise

  # Updates the lifecycle config, creating one if it doesn't already exist.
  def update_lifecycle_config(self, rule_id, rule, override_rule=False):
    lifecycle = self.get_lifecycle_config()
    existing_rule = next((r for r in lifecycle['Rules'] if r['ID'] == rule_id),None)
    if existing_rule is None:
      lifecycle['Rules'].append(rule)
    else:
      if override_rule == False:
        return

      existing_rule = rule

    self.s3_client.put_bucket_lifecycle_configuration(
        Bucket=self.default_bucket_name,
        LifecycleConfiguration=lifecycle)
