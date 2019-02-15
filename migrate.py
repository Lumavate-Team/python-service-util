from alembic.command import history, downgrade, upgrade
from contextlib import redirect_stdout, redirect_stderr
from lumavate_service_util import RestBehavior
from flask import render_template, g
from alembic.config import Config
from io import StringIO
import sys
import os

ALEMBIC_CONFIG = os.getenv('ALEMBIC_CONFIG', '/app/alembic.ini')

class LumavateMigrate(RestBehavior):
  def __init__(self):
    self.user=g.token_data.get('user')
    self.role=g.token_data.get('role')
    self.org_type=g.token_data.get('orgType')
    self.namespace=g.token_data.get('namespace')

    super().__init__(None)

  def get_alembic_config(self):
    config = Config(ALEMBIC_CONFIG, stdout=StringIO())
    config.format_stdout = lambda: config.stdout.getvalue().splitlines()
    return config

  def history(self, template=None, template_args=None):
    config = self.get_alembic_config()
    history(config)
    if template is None:
      template = 'manage.html'
    if template_args is None:
      template_args = {
          "user": self.user,
          "role": self.role,
          "org_type": self.org_type,
          "namespace": self.namespace
          }

    try:
      return render_template(template, **template_args, output=config.format_stdout())

    except Exception as e:
      print(e, flush=True)
      return "Error Rendering Template: \
          If you are using a custom template, \
          be sure it is located in the /app/templates folder. \
          Template Name: {}".format(e)

  def current_revision(self, template=None, template_args=None):
    config = self.get_alembic_config()
    f = StringIO()
    with redirect_stderr(f):
      current(config)

    if template is None:
      template = 'manage.html'
    if template_args is None:
      template_args = {
          "user": self.user,
          "role": self.role,
          "org_type": self.org_type,
          "namespace": self.namespace
          }

    return render_template(template, **template_args, output=f.getvalue().splitlines())

  def upgrade(self, template=None, template_args=None):
    config = self.get_alembic_config()
    f = StringIO()
    with redirect_stderr(f):
      upgrade(config, '+1')

    if template is None:
      template = 'manage.html'
    if template_args is None:
      template_args = {
          "user": self.user,
          "role": self.role,
          "org_type": self.org_type,
          "namespace": self.namespace
          }

    return render_template(template, **template_args, output=f.getvalue().splitlines())

  def downgrade(self, template=None, template_args=None):
    config = self.get_alembic_config()
    f = StringIO()
    with redirect_stderr(f):
      downgrade(config, '-1')

    if template is None:
      template = 'manage.html'
    if template_args is None:
      template_args = {
          "user": self.user,
          "role": self.role,
          "org_type": self.org_type,
          "namespace": self.namespace
          }

    return render_template(template, **template_args, output=f.getvalue().splitlines())
