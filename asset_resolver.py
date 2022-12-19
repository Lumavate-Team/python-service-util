from .request import get_lumavate_request
from flask import request, g

class AssetResolver():
  def __init__(self):
    self._containers = {}
    self._data = None

  def resolve(self, data):
    if not 'containerId' in data or not 'assetId' in data or not 'assetType' in data:
      return lambda: None
    
    container_id = data['containerId']
    asset_id = data['assetId']
    asset_type = data['assetType']

    if container_id not in self._containers:
      self._containers[container_id] = {'asset_type': asset_type, 'asset_ids': []}

    self._containers[container_id]['asset_ids'].append(asset_id)
    return lambda: self.do_resolve(container_id, asset_id)

  def lookup_data(self):
    containers = []
    payload = {'references': containers}
    for id, data in self._containers.items():
      containers.append({'containerId': id, 'assetType': data['asset_type'], 'assetIds': data['asset_ids']})

    headers = {
      'Authorization': request.headers['Authorization'],
      'Content-Type': 'application/json'
    }

    self._data = get_lumavate_request().post('/iot/v1/assets/resolve', payload=payload, headers=headers)['resolvedContainers']

  def do_resolve(self, container_id, asset_id):
    if self._data is None:
      self.lookup_data()

    return self._data.get(str(container_id), {}).get('assets', {}).get(str(asset_id), {})

