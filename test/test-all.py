from org.webpki.cbor import CBOR

def assert_true(text, expression):
  if not expression:
    raise Exception("Failed on: " + text)
  
def assert_false(text, expression):
  if expression:
    raise Exception("Failed on: " + text)
  
def fail(text):
  raise Exception("Failed on: " + text)

__name = ''
def success():
  print('Test ' + __name + ' was successful')

__count = 0

TESTS = [
['integer.py',
"""
# Test program for integer "edge cases"

def one_turn(value, expected):
  text = str(value)
  while len(text) < 25:
    text += ' '
  cbor = CBOR.Int(value).encode()
  got = cbor.hex()
  if got != expected:
    got = '***=' + got
  else:
    got = ''
  # assert_true("Failed decoding: " + value, CBOR.decode(cbor).get_big_integer() == value)
  while len(expected) < 20:
    expected += ' '
  if len(got):
    fail(text + expected + got)

# -0 is treated as 0 for integers
assert_true("minus-0", CBOR.Int(-0).encode().hex() == "00")
one_turn(0, '00')
one_turn(-1, '20')
one_turn(255, '18ff')
one_turn(256, '190100')
one_turn(-256, '38ff')
one_turn(-257, '390100')
one_turn(1099511627775, '1b000000ffffffffff')
one_turn(18446744073709551615, '1bffffffffffffffff')
one_turn(18446744073709551616, 'c249010000000000000000')
one_turn(-18446744073709551616, '3bffffffffffffffff')
one_turn(-18446744073709551617, 'c349010000000000000000')


success()

"""],
['kurt.py',
"""
from org.webpki.cbor import CBOR

##########################
#       Testing...       #
##########################

i = CBOR.Int(50)
print(i.encode().hex())

print(i.get_int8())

s = CBOR.String("kurt€")
print(s.encode().hex())

# print(s.get_int8())

a = CBOR.Array()
a.add(i).add(s)
print(a.encode().hex())

f = CBOR.Float(2.0e50)
print(f.get_float64())
print(f.encode().hex())

print(CBOR.Bytes(bytes([0,1,0x99])).encode().hex())

k = CBOR.Int(7)
k.get_int8()
k.check_for_unread()

CBOR.decode("DEC".encode("utf8"))

import http.client
conn = http.client.HTTPSConnection("cyberphone.github.io")
conn.request("GET", "/javaapi/app-notes/large-payloads/metadata.cbor")
response = conn.getresponse()
print(response.status, response.reason)
CBOR.init_decoder(response, 10000).decode_with_options()

print(CBOR.NonFinite(0x7ff0000000000000).encode().hex())
print(CBOR.NonFinite.create_payload(0x1).encode().hex())
print(CBOR.NonFinite.create_payload((1 << 10) - 1).encode().hex())
print(CBOR.NonFinite.create_payload((1 << 23) - 1).encode().hex())
print(CBOR.NonFinite.create_payload(1 << 10).encode().hex())
print(CBOR.NonFinite.create_payload((1 << 52) - 1).encode().hex())
print(CBOR.NonFinite.create_payload((1 << 52) - 1).set_sign(True).encode().hex())
print(CBOR.NonFinite.create_payload((1 << 53) - 1).encode().hex())
print(CBOR.NonFinite.create_payload((1 << 52) + 1).encode().hex())
print(CBOR.NonFinite.create_payload(1 << 23).encode().hex())

print(CBOR.NonFinite.create_payload(123456789).get_payload())

print(CBOR.NonFinite.create_payload(123456789).get_payload())

print(CBOR.version)

success()

"""]]

for o in TESTS:
  __name = o[0]
  print(o[0])
  try:
    exec(o[1])
  except Exception:
    print("Failed '" + __name + "'")
    __count += 1
if (__count):
  print("***ERRORS*** " + str(__count))
else:
  print("SUCCESSFUL")
