from .request import get_lumavate_request
from flask import g, request
import os
import rollbar

class Email():
  def __init__(self):
    pass

  def send_email(self, recipients, subject, body):
    notification_url = f'{os.environ.get("PROTO")}{request.host}/iot/v1/send-system-email'
    
    if not isinstance(recipients, list):
      recipients = recipients.split(',')

    email_data = {
      'toAddresses': recipients,
      'subject': subject,
      'htmlContent': body
    }

    try:
      get_lumavate_request().post(notification_url, payload=email_data)
    except Exception as e:
      rollbar.report_message(f'Error sending email: {e}')

    return

    



