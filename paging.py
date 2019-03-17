from flask import request, current_app, make_response, jsonify
from urllib.parse import urlparse, parse_qs
import os

class Paging:
  @property
  def page(self):
    page = int(request.args.get('page')) if request.args.get('page') is not None and request.args.get('page').isdigit() else 1
    if page < 1:
      page = 1

    return page

  @property
  def page_size(self):
    page_size = int(request.args.get('pagesize')) if request.args.get('pagesize') is not None and request.args.get('pagesize').isdigit() else current_app.config.get('DEFAULT_PAGESIZE', 100)
    if page_size < 1:
      page_size = current_app.config.get('DEFAULT_PAGESIZE', 100)

    return page_size

  def run(self, query, serialize_func=None):
    paged_data = query.paginate(self.page, self.page_size, False)
    base_url = '{}{}'.format(os.environ.get('PROTO'),request.base_url[7:])
    next_params =  self.get_query_params(request.url, paged_data, next_page=True)
    prev_params =  self.get_query_params(request.url, paged_data)

    response = { 'payload':
                  { 'data' : [],
                    'page': self.page,
                    'pageSize': self.page_size,
                    'totalPages': paged_data.pages,
                    'totalItems': paged_data.total,
                    'currentItemCount': len(paged_data.items),
                    'nextPage': base_url + next_params if paged_data.has_next else None,
                    'prevPage': base_url + prev_params if paged_data.has_prev else None
                  }
              }

    for r in paged_data.items:
      if serialize_func is None:
        response['payload']['data'].append(r.to_json())
      else:
        response['payload']['data'].append(serialize_func(r))

    return make_response(jsonify(response), 200)

  def get_query_params(self, url, paged_data, next_page = False):
    o = urlparse(url)
    query = parse_qs(o.query)
    params = '?'
    previousPage = str(paged_data.pages) if self.page > paged_data.pages else str(paged_data.prev_num)

    for param, value in query.items():
      if param !='page' and param !='pagesize':
        if params == '?':
          params+=param+'='+value[0]
        else:
          params += '&'+param + '=' + value[0]

    if params != '?':
      params += '&'

    if next_page:
      params += 'page=' + str(paged_data.next_num) + '&pagesize=' + str(self.page_size)
    else:
      params += 'page=' + previousPage + '&pagesize=' + str(self.page_size)

    return params
