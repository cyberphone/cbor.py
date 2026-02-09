from org.webpki.cbor import CBOR
import math

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
  assert_true("Failed decoding: " + str(value), CBOR.decode(cbor).get_big_integer() == value)
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

try:
  CBOR.Int(1.1)
  fail("Should not")
except Exception as error:
  assert_true("msg1" + repr(error), repr(error).find("Expected 'int', got 'float'") >= 0)

try:
  CBOR.Int("10")
  fail("Should not")
except Exception as error:
  assert_true("msg2" + repr(error), repr(error).find("Expected 'int', got 'str'") >= 0)

try:
  CBOR.Int(1, 7)
  fail("Should not")
except TypeError as error:
  pass

success()

"""],
['int-ranges.py',
"""
# Testing range-constrained integers


def goodRun(type, value):
  bigFlag = type.find("64") > 0 or type.find("128") > 0
  wrapper = CBOR.decode(CBOR.Int(value).encode())
  test = 'assert_true("good", wrapper.get' + type + '() == ' + \\
    str(value) + ')'
  eval(test)
  test = 'CBOR.Int.create' + type + '(' + str(value) + ')'
  eval(test)
  if value == 10:
    test = 'CBOR.Int.create' + type + '(' + str(value) +')'
    eval(test)

def badRun(type, value):
  wrapper = CBOR.decode(CBOR.Int(value).encode())
  test = 'wrapper.get' + type + '()'
  try:
    eval(test)
    fail("Should fail");
  except Exception as error:
    if repr(error).find('Value out of range') < 0:
      raise Exception(error)
  test = 'CBOR.Int.create' + type + '(' + str(value) + ')'
  try:
    eval(test)
    fail("Should fail")
  except Exception as error:
    if repr(error).find('Value out of range') < 0:
      raise Exception(error)

def innerTurn(type, signed, size):
  min_val = -(1 << size - 1) if signed else 0
  max_val = (1 << size - 1) - 1 if signed else (1 << size) - 1
  if size == 53:
    max_val = 0x1fffffffffffff
    min_val = -max_val
  goodRun(type, min_val)
  goodRun(type, max_val)
  goodRun(type, 10)
  badRun(type, max_val + 1)
  badRun(type, min_val - 1)

def oneTurn(size):
  innerTurn("_int" + str(size), True, size)
  if size != 53:
    innerTurn("_uint" + str(size), False, size)

oneTurn(8)
oneTurn(16)
oneTurn(32)
oneTurn(53)
oneTurn(64)
oneTurn(128)

success()
"""],
['xyz-encoder.py',
"""
# Simple "encoder" API

class XYZEncoder:

  COUNTER     = CBOR.Int(1)
  TEMPERATURE = CBOR.Int(2)
  GREETING    = CBOR.Int(3)

  def __init__(self):
    self._map = CBOR.Map()

  def set_counter(self, intVal):
    self._map.set(XYZEncoder.COUNTER, CBOR.Int.create_uint8(intVal))
    return self

  def set_temperature(self, floatVal):
    self._map.set(XYZEncoder.TEMPERATURE, CBOR.Float(floatVal))
    return self

  def set_greeting(self, stringVal):
    self._map.set(XYZEncoder.GREETING, CBOR.String(stringVal))
    return self

  def build(self):
    assert_true("incomplete", self._map.length == 3)
    return self._map.encode()

# Using the "builder" pattern:
cbor = (XYZEncoder()          
      .set_counter(2)           
      .set_greeting('Hi!')      
      .set_temperature(53.0001) 
      .build())

assert_true("bad code", cbor.hex() == 'a3010202fb404a800346dc5d640363486921')

success()
"""],
['xyz-decoder.py',
"""
# Simple "decoder" API

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
    return self._greeting;

cbor = bytes.fromhex('a3010202fb404a800346dc5d640363486921')

xyz = XYZDecoder(cbor)

assert_true("counter", xyz.counter == 2)
assert_true("temperature", xyz.temperature == 53.0001)
assert_true("greeting", xyz.greeting == 'Hi!')

success()
"""]]

for o in TESTS:
  __name = o[0]
  try:
    exec(o[1])
  except Exception:
    print("Failed '" + __name + "'")
    __count += 1
if (__count):
  print("***ERRORS*** " + str(__count))
else:
  print("SUCCESSFUL")
