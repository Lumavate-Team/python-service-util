from .request import get_lumavate_request
from flask import request, g
import copy

class AssetResolver():
  def __init__(self):
    self._containers = {}
    self._data = None
    # this is used to determine if a resolved asset should be pushed all the way back as the field value(app), or just the assetRef(platform)
    # it has to be done here due to the resolves switching scope
    is_app_scope = False
    if g:
      is_app_scope = g.get('token_data',{}).get('scope','') == 'runtime'
  
    self.is_app_scope = is_app_scope

  def resolve(self, asset_ref):
    #otherwise asset_ref.asset will recurse
    asset_ref = copy.deepcopy(asset_ref)

    if not asset_ref or not 'containerId' in asset_ref or not 'assetId' in asset_ref or not 'assetType' in asset_ref:
      return lambda: None
    container_id = asset_ref['containerId']
    asset_id = asset_ref['assetId']
    asset_type = asset_ref['assetType']

    if container_id not in self._containers:
      self._containers[container_id] = {'asset_type': asset_type, 'asset_refs': []}

    self._containers[container_id]['asset_refs'].append(asset_ref)
    return lambda: self.do_resolve(container_id, asset_id)

  def lookup_data(self):
    containers = []
    payload = {'references': containers}
    for id, data in self._containers.items():
      containers.append({'containerId': id, 'assetType': data['asset_type'], 'assetRefs': data['asset_refs']})

    headers = {
      'Authorization': request.headers['Authorization'],
      'Content-Type': 'application/json'
    }

    self._data = get_lumavate_request().post('/iot/v1/assets/resolve', payload=payload, headers=headers)['resolvedContainers']

  def do_resolve(self, container_id, asset_id):
    if self._data is None:
      self.lookup_data()

    return self._data.get(str(container_id), {}).get('assets', {}).get(str(asset_id), {}).get('asset', {})

