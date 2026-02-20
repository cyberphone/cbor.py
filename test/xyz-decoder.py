# Simple "decoder" API
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success

class XYZDecoder:

  COUNTER     = CBOR.Int(1)
  TEMPERATURE = CBOR.Int(2)
  GREETING    = CBOR.Int(3)

  def __init__(self, cbor):
    # There MUST be exactly three key/value pairs.
    # CBOR data items are type-checked as well.
    map = CBOR.decode(cbor)
    # If the top-level object is not a CBOR map, the next
    # JavaScript line will throw an exception because there is
    # only one get-method that has a CBOR wrapper as input parameter.
    self._counter = map.get(XYZDecoder.COUNTER).get_uint8()
    self._temperature = map.get(XYZDecoder.TEMPERATURE).get_float64()
    self._greeting = map.get(XYZDecoder.GREETING).get_string()
    # We got more than we asked for?
    map.check_for_unread()

  @property
  def counter(self):
    return self._counter

  @property
  def temperature(self):
    return self._temperature

  @property
  def greeting(self):
    return self._greeting

cbor = bytes.fromhex('a3010202fb404a800346dc5d640363486921')

xyz = XYZDecoder(cbor)

assert_true("counter", xyz.counter == 2)
assert_true("temperature", xyz.temperature == 53.0001)
assert_true("greeting", xyz.greeting == 'Hi!')

success()
