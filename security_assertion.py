from flask import g, request
from lumavate_exceptions import InvalidOperationException
from .request import get_lumavate_request, LumavateRequest
import os

class SecurityAssertion:
  def __init__(self):
    self._rolemap = {}

  def load_rolemap(self):
    pass

  def get_all_auth_groups(self):
    try:

      if g.token_data.get('authUrl') is '':
        auth_groups = []

        return auth_groups

      elif g.token_data.get('authUrl', '').startswith('http'):
        auth_route = g.token_data.get('authUrl') + 'discover/auth-groups'
      else:
        auth_route = '/'.join(g.token_data.get('authUrl').strip('/').split('/')[:2])
        auth_route = os.environ.get('PROTO') + request.host + '/' + auth_route + '/discover/auth-groups'

      auth_groups = LumavateRequest().get(auth_route)
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

    print('required: {}'.format(required_roles),flush=True)
    user_groups = g.auth_status.get('roles')
    user_groups.append('__all__')
    print('groups: {}'.format(user_groups),flush=True)

    return len(list(set(user_groups) & set(required_roles))) > 0

  def assert_has_role(self, roles):
    if not self.has_role(roles):
      raise InvalidOperationException('Insuffucient Privileges')
