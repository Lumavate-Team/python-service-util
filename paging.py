from flask import request, current_app, make_response, jsonify

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
    previousPage = str(paged_data.pages) if self.page > paged_data.pages else str(paged_data.prev_num)

    response = { 'payload':
                  { 'data' : [],
                    'page': self.page,
                    'pageSize': self.page_size,
                    'totalPages': paged_data.pages,
                    'totalItems': paged_data.total,
                    'currentItemCount': len(paged_data.items),
                    'nextPage': request.base_url + '?page=' + str(paged_data.next_num) + '&pagesize=' + str(self.page_size) if paged_data.has_next else None,
                    'prevPage': request.base_url + '?page=' + previousPage + '&pagesize=' + str(self.page_size) if paged_data.has_prev else None
                  }
              }

    for r in paged_data.items:
      if serialize_func is None:
        response['payload']['data'].append(r.to_json())
      else:
        response['payload']['data'].append(serialize_func(r))

    return make_response(jsonify(response), 200)

