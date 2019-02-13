from lumavate_service_util import RestBehavior
from flask import render_template, g
from alembic.command import history, downgrade, upgrade
from alembic.config import Config
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import sys

ALEMBIC_CONFIG = '/app/alembic.ini'

class LumavateMigrate(RestBehavior):
  def __init__(self):
    super().__init__(None)

  def get_alembic_config(self):
    config = Config(ALEMBIC_CONFIG, stdout=StringIO())
    config.format_stdout = lambda: config.stdout.getvalue().splitlines()
    return config

  def history(self):
    config = self.get_alembic_config()
    history(config)
    return render_template('manage.html', \
      user=g.token_data.get('user'), \
      role=g.token_data.get('role'), \
      org_type=g.token_data.get('orgType'), \
      namespace=g.token_data.get('namespace'), \
      output=config.format_stdout())

  def upgrade(self):
    config = self.get_alembic_config()
    f = StringIO()
    with redirect_stderr(f):
      upgrade(config, 'head')

    return render_template('manage.html', \
      user=g.token_data.get('user'), \
      role=g.token_data.get('role'), \
      org_type=g.token_data.get('orgType'), \
      namespace=g.token_data.get('namespace'), \
      output=f.getvalue().splitlines())

  def downgrade(self):
    config = self.get_alembic_config()
    f = StringIO()
    with redirect_stderr(f):
      downgrade(config, 'base')

    return render_template('manage.html', \
      user=g.token_data.get('user'), \
      role=g.token_data.get('role'), \
      org_type=g.token_data.get('orgType'), \
      namespace=g.token_data.get('namespace'), \
      output=f.getvalue().splitlines())
