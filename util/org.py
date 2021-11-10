from flask import g
#from hashids import Hashids

def org_hash(org_id=None):
  org_id = org_id or g.org_id

  return ''
  """
  return Hashids(min_length=4,
    salt='T2uDF0uSWF8RwU6IdL0x',
    alphabet='abcdefghijklmnopqrstuvwxyz1234567890').encode(org_id)
  """

