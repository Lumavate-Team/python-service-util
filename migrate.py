from alembic.command import history, downgrade, upgrade, current
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

    if os.path.isdir("/app/templates"):
      self.default = False
    else:
      self.default = True

    super().__init__(None)

  def get_alembic_config(self):
    config = Config(ALEMBIC_CONFIG, stdout=StringIO())
    config.format_stdout = lambda: config.stdout.getvalue().splitlines()
    return config

  def history(self, template=None, template_args=None):
    config = self.get_alembic_config()
    history(config)

    if self.default:
      template = 'manage.html'
      template_args = {
          "user": self.user,
          "role": self.role,
          "org_type": self.org_type,
          "namespace": self.namespace
          }

      return render_template(template, **template_args, output=config.format_stdout())

    else:
      return config.format_stdout()

  def current_revision(self, template=None, template_args=None):
    config = self.get_alembic_config()
    f = StringIO()
    with redirect_stderr(f):
      current(config, verbose=True)

    return f.getvalue().splitlines()

  def upgrade(self, template=None, template_args=None):
    config = self.get_alembic_config()
    f = StringIO()
    target = self.get_data().get('target')
    if target is None:
      return

    if target != "head":
      with redirect_stderr(f):
        upgrade(config, '+{}'.format(target))
    else:
      with redirect_stderr(f):
        upgrade(config, 'head')

    return f.getvalue().splitlines()

  def downgrade(self, template=None, template_args=None):
    config = self.get_alembic_config()
    f = StringIO()

    target = self.get_data().get('target')
    if target is None:
      return

    if target != "base":
      with redirect_stderr(f):
        downgrade(config, '-{}'.format(target))
    else:
      with redirect_stderr(f):
        downgrade(config, 'base')

    return f.getvalue().splitlines()
