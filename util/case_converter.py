import re
camel_pat = re.compile(r'([A-Z0-9])')
under_pat = re.compile(r'_([A-Za-z0-9])')
hyphen_pat = re.compile(r'-([A-Za-z0-9])')

# Helper functions
def underscore_to_camel(name):
  return under_pat.sub(lambda x: x.group(1).upper(), name)

def camel_to_underscore(name):
  return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)

def hyphen_to_camel(name):
  return hyphen_pat.sub(lambda x: x.group(1).upper(), name)