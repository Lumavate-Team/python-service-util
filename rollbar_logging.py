from flask import got_request_exception, Request, g
from app import app
import rollbar
import rollbar.contrib.flask
import os

def is_rollbar_configured():
  if os.environ.get("ROLLBAR_TOKEN", None) and os.environ.get("ROLLBAR_ENVIRONMENT", None):
    return True
  else:
    return False

def init_rollbar():
  """init rollbar module"""
  if is_rollbar_configured():
    rollbar.init(
      os.environ.get("ROLLBAR_TOKEN", None),
      os.environ.get("ROLLBAR_ENVIRONMENT",None),
      # server root directory, makes tracebacks prettier
      root=os.path.dirname(os.path.realpath(__file__)),
      # flask already sets up logging
      allow_logging_basic_config=False
      )
    # send exceptions from `app` to rollbar, using flask's signal system.
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)
  else:
    print(f'rollbar failed to initialize. \
      ROLLBAR_TOKEN: {os.environ.get("ROLLBAR_TOKEN", None)}, \
      ROLLBAR_ENVIRONMENT: {os.environ.get("ROLLBAR_ENVIRONMENT", None)}', flush=True)


class RollbarRequest(Request):
    @property
    def rollbar_person(self):
        # 'id' is required, 'username' and 'email' are indexed but optional.
        # all values are strings.
        user_id = 'anonymous'
        if g.get('auth_status'):
          user_id = g.auth_status.get('user', 'anonymous')

        return {'id': user_id}