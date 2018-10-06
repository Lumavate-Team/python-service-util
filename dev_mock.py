from lumavate_properties import Properties, Components
from lumavate_service_util import LumavateMockRequest, set_lumavate_request_factory
from lumavate_token import AuthToken
import json

class ServiceData():
  def __init__(self, sd):
    self._sd = sd

  def set_property(self, name, value):
    self._sd['serviceData'][name] = value
    return self

  def append_component(self, name, componentType, componentData):
    data = {
      'componentType': componentType,
      'componentData': componentData
    }
    self._sd['serviceData'][name].append(data)
    return self

  def data(self):
    return self._sd

class DevMock():
  def __init__(self, properties):
    self._properties = properties
    set_lumavate_request_factory(self.get_mock_lumavate_request)

  def get_auth_token(self):
    auth_token = AuthToken()
    auth_token.namespace = 'abc'
    auth_token.session = 'localhost'
    auth_token.code = 'localhost'
    auth_token.org_id = 1
    auth_token.version = 'production'
    auth_token.home_url = ''
    auth_token.auth_url = ''
    return auth_token

  def get_auth_data(self):
    return {
      'status': 'inactive',
      'roles': [],
      'user': 'anonymous'
    }

  def get_property_data(self):
    payload = {'data': {}}
    for p in self._properties:
      prop = Properties.Property.from_json(p)
      payload['data'][prop.name] = prop.read({})

    sd = ServiceData({
      'serviceData': payload['data'],
      'session': {
        'lastIp': '104.137.209.245'
      },
      'sutValid': True
    })
    return sd

  def get_mock_lumavate_request(self):
    t = self.get_auth_token()
    data = self.get_property_data()
    auth_data = self.get_auth_data()

    return LumavateMockRequest(data.data(), auth_data, t.get_token())
