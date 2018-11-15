from flask import g, request
from lumavate_exceptions import InvalidOperationException
from .request import get_lumavate_request
import os

class SecurityAssertion:
  def __init__(self):
    self._rolemap = {}

  def load_rolemap(self):
    pass

  def get_all_auth_groups(self):
    try:
      auth_route = '/'.join(g.token_data.get('authUrl').strip('/').split('/')[:2])
      auth_groups = get_lumavate_request().get(os.environ.get('PROTO') + request.host + '/' + auth_route + '/discover/auth-groups')
    except Exception as e:
      print(e, flush=True)
      auth_groups = []

    auth_groups = [{'value': x['name'], 'displayValue': x['name']} for x in auth_groups]
    auth_groups.append({'value': '__all__', 'displayValue': 'All Users'})

    return auth_groups

  def has_role(self, roles):
    self.load_rolemap()
    if isinstance(roles, str):
      roles = [roles]

    required_roles = []
    for r in roles:
      required_roles = required_roles + self._rolemap.get(r, [])

    user_groups = g.auth_status.get('roles')

    return len(list(set(user_groups) & set(required_roles))) > 0

  def assert_has_role(self, roles):
    if not self.has_role(roles):
      raise InvalidOperationException('Insuffucient Privileges')
