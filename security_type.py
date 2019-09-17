from enum import Enum

class SecurityType(Enum):
  browser_origin = 1
  api_origin = 2
  system_origin = 3
  signed=100
  sut=101
  jwt=102
  none=103