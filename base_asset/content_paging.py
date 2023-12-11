from flask_sqlalchemy import BaseQuery
from flask import request, current_app, make_response, jsonify
from sqlalchemy import func
from urllib.parse import urlparse, parse_qs
import os
from ..paging import Paging
from ..db import db
import json
from math import ceil

class ContentPaging(Paging):
  def run(self, query, serialize_func=None):
    paged_data = query.limit(self.page_size).offset((self.page * self.page_size) - self.page_size)
    total_items = db.session.query(func.count(query.subquery().columns.id).label("total_cnt")).scalar()
    total_pages = ceil(total_items / self.page_size)

    base_url = '{}{}'.format(os.environ.get('PROTO'),request.base_url[7:])

    previous_page = None if self.page <= 1 else str(self.page - 1)
    next_page = None if self.page >= total_pages else str(self.page + 1)

    next_params =  self.get_query_params(request.url, next_page)
    prev_params =  self.get_query_params(request.url, previous_page)

    response = { 'payload':
                  { 
                    'data' : [],
                    'page': self.page,
                    'pageSize': self.page_size,
                    'totalPages': ceil(total_items / self.page_size),
                    'totalItems': total_items,
                    'nextPage': base_url + next_params if next_page else None,
                    'prevPage': base_url + prev_params if previous_page else None
                  }
              }

    for r in db.session.execute(paged_data).fetchall():
      if serialize_func is None:
        response['payload']['data'].append(dict(r))
      else:
        response['payload']['data'].append(serialize_func(dict(r)))

    response['payload']['currentItemCount'] = len(response['payload']['data'])
    return make_response(jsonify(response), 200)

  def get_query_params(self, url, page):
    o = urlparse(url)
    query = parse_qs(o.query)
    params = '?'

    for param, value in query.items():
      if param !='page' and param !='pagesize':
        if params == '?':
          params+=param+'='+value[0]
        else:
          params += '&'+param + '=' + value[0]

    if params != '?':
      params += '&'

    params += 'page=' + str(page) + '&pagesize=' + str(self.page_size)

    return params