from .request import get_lumavate_request

class Resolver:
  def __init__(self, api_route, format_func = None, headers = None):
    self._api_route = api_route
    self._ids = []
    self._data = None
    self._format_func = format_func if format_func is not None else lambda x: x
    self._headers = headers

  def resolve(self, id):
    self._ids.append(str(id).split('!')[-1])
    return lambda: self.do_resolve(id)

  def lookup_data(self):
    url = self._api_route
    if '?' in url:
      url = url + '&id=' + '||'.join(self._ids)
    else:
      url = url + '?id=' + '||'.join(self._ids)

    self._data = get_lumavate_request().get(url, headers=self._headers)

  def do_resolve(self, id):
    if self._data is None:
      self.lookup_data()

    data = next((x for x in self._data if x['id'] == id), None)
    return self._format_func(data)
