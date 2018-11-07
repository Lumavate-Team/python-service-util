from flask import g, request
from lumavate_exceptions import InvalidOperationException
import os

class SecurityAssertion:
  def __init__(self):
    self._rolemap = {}
    self.load_rolemap()

  def load_rolemap(self):
    pass

  def get_all_auth_groups(self):
    try:
      auth_route = '/'.join(g.token_data.get('authUrl').strip('/').split('/')[:2])
      auth_groups = LumavateRequest().get(os.environ.get('PROTO') + request.host + '/' + auth_route + '/discover/auth-groups')
    except Exception as e:
      auth_groups = []

    auth_groups = [{'value': x['name'], 'displayValue': x['name']} for x in auth_groups]
    auth_groups.append({'value': '__all__', 'displayValue': 'All Users'})

    return auth_groups

  def assert_has_role(self, role):
    user_groups = g.auth_status.get('roles')
    required_groups = self._rolemap.get(role, [])

    if len(list(set(user_groups) & set(required_groups))) == 0:
      raise InvalidOperationException('User missing role "' + role + '"')
