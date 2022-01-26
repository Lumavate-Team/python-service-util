from .request import get_lumavate_request
from flask import g, request
import boto3
import os
import rollbar

class Email():
  def __init__(self):
    pass

  def send_email(self, recipients, subject, body):
    notification_url = f'{os.environ.get("PROTO")}{request.host}/iot/v1/send-system-email'
    
    if not isinstance(recipients, list):
      recipients = recipients.split(',')
      
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')

    if not aws_access_key_id:
      rollbar.report_message('AWS_ACCESS_KEY_ID is not set attempting when send an email')
      return

    if aws_access_key_id == 'dev-key':
      print('Subject: ', subject, flush=True)
      print('To: ', recipients, flush=True)
      print('Message: ', body, flush=True)
    else:
      try:
        region_name = os.environ.get('AWS_REGION')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

        if not region_name or not aws_secret_access_key:
          rollbar.report_message('Environment is not configured for attempting to send an email')
          return

        client = boto3.client('ses',
          region_name=region_name,
          aws_access_key_id=aws_access_key_id,
          aws_secret_access_key=aws_secret_access_key)

        client.send_email(
          Destination={
            'ToAddresses': recipients
          },
          Message={
            'Body': {
              'Html': {
                'Data': body,
              }
            },
            'Subject': {
                'Data': subject,
            },
          },
          Source='noreply@' + request.host.replace('_', '-')
        )

      except Exception as e:
        rollbar.report_message(f'Error sending email: {e}')

    return { 'status': 'sent' }

    



