from flask import g
from hashids import Hashids

def org_hash(org_id=None):
  id = org_id if org_id is not None else g.org_id

  return Hashids(min_length=4,
    salt='T2uDF0uSWF8RwU6IdL0x',
    alphabet='abcdefghijklmnopqrstuvwxyz1234567890').encode(id)

