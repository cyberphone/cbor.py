from org.webpki.cbor import CBOR
import math
import struct
import io

def assert_true(text, expression):
  if not expression:
    raise Exception("Failed on: " + text)
  
def assert_false(text, expression):
  if expression:
    raise Exception("Failed on: " + text)
  
def fail(text):
  raise Exception("Failed on: " + text)

def check_exception(exception, expected, throw=True):
  if repr(exception).find(expected) >= 0:
    return True
  if throw:
    raise Exception("Expected '{:s}', got '{:s}'".format(expected, repr(exception)))
  return False

__name = ''
def success():
  print('Test ' + __name + ' was successful')

__count = 0

TESTS = [
['arrays.py',
"""
# Testing array operations


array = CBOR.Array().add(CBOR.String("three")).add(CBOR.String("four"))
assert_true("size-0", array.length == 2)
assert_true("get-0", array.get(0).get_string() == "three")
assert_true("get-1", array.get(1).get_string() == "four")
arrayElements = array.to_array()
assert_true("size-1", len(arrayElements) == 2)
assert_true("arr-0", arrayElements[0].get_string() == "three")
assert_true("arr-1", arrayElements[1].get_string() == "four")
assert_true("upd-1", array.update(1, CBOR.Int(1)).get_string() == "four")
assert_true("upd-2", array.get(1).get_int8() == 1)
assert_true("size-1", array.length == 2)
assert_true("upd-3", array.get(0).get_string() == "three")
assert_true("upd-4", array.insert(array.length, CBOR.Int(-8)) == array)
assert_true("upd-5", array.get(array.length - 1).equals(CBOR.Int(-8)))
assert_true("upd-4", array.insert(0, CBOR.Int(-9)) == array)
assert_true("upd-5", array.get(0).equals(CBOR.Int(-9)))
l = array.length
assert_true("upd-6", array.remove(0).equals(CBOR.Int(-9)))
assert_true("upd-7", l == array.length + 1)
assert_true("upd-8", array.get(0).get_string() == "three")
assert_true("upd-9", array.to_diagnostic(False) == '["three",1,-8]')

def aBadOne(expression):
  try:
    eval("array." + expression)
    fail("Should not pass")
  except Exception:
    pass

aBadOne("get('string')")
aBadOne("get(array.length)")
aBadOne("get(-1)")
aBadOne("insert(array.length + 1, CBOR.Int(6))")
aBadOne("insert(array.length)")
aBadOne("remove(array.length)")
aBadOne("remove(array.length - 1, 'hi')")
aBadOne("get(0, 6)")

success()
"""],
['float.py',
"""
# Test program for floating-point "edge cases"

def overflow(decodedValue, length):
  test = 'decodedValue.get_float' + length + '()'
  try:
    eval(test)
    fail("Should fail")
  except Exception as e:
    check_exception(e, "Value out of range for \\"float")

def shouldpass(decodedValue, value, length, valueText):
  assert_true("p1", float(decodedValue.to_string()) == float(valueText))
  test = 'decodedValue.get_float' + length + '()'
  float_value = eval(test)
  assert_true("p2", float_value == value)
  if length == "64":
    test = 'decodedValue.get_extended_float' + length + '()'
    float_value = eval(test)
    assert_true("p3", float_value == value)

def oneTurn(valueText, expected):
  value = float(valueText)
  if math.isfinite(value):
    try:
      CBOR.NonFinite(value)
      fail("f1")
    except Exception as e:
      check_exception(e, "float")
  
    cbor = CBOR.Float(value).encode()
    assert_true("f3", cbor.hex() == expected)
    decodedValue = CBOR.decode(cbor)
    match len(cbor):
      case 3:
        shouldpass(decodedValue, value, "16", valueText)
        shouldpass(decodedValue, value, "32", valueText)
        shouldpass(decodedValue, value, "64", valueText)

      case 5:
        shouldpass(decodedValue, value, "32", valueText)
        shouldpass(decodedValue, value, "64", valueText)
        overflow(decodedValue, "16")

      case 9:
        shouldpass(decodedValue, value, "64", valueText)
        overflow(decodedValue, "16")
        overflow(decodedValue, "32")

      case _:
        fail("No such length")
  else:
    try:
      CBOR.Float(value)
      fail('Should not execute')
    except Exception as e:
      check_exception(e, "Not permitted: 'NaN/Infinity'")

    decodedValue = CBOR.Float.create_extended_float(value)
    assert_true("nf2", str(decodedValue.get_extended_float64()) == str(value))
    assert_true("nf3", decodedValue.to_string() == valueText)
    cbor = decodedValue.encode()
    assert_true("nf4", cbor.hex() == expected)
    assert_true("nf5", CBOR.decode(cbor) == decodedValue)
    buf = struct.pack("!d", value)
    assert_true("nf6", decodedValue.get_non_finite64() == CBOR._bytes_to_uint(buf))
    assert_true("d10", CBOR.Float.create_extended_float(value).encode().hex() == expected)

def payloadOneTurn(payload, hex, dn):
  dn = ("float'" + hex[2:] + "'") if dn == None else dn
  cbor = CBOR.NonFinite.create_payload(payload).encode()
  object = CBOR.decode(cbor)
  assert_true("plo1", isinstance(object, CBOR.NonFinite))
  nonFinite = object
  assert_true("plo2", nonFinite.get_payload() == payload)
  assert_true("plo3", cbor.hex() == hex)
  assert_true("plo4", nonFinite.to_string() == dn)
  assert_true("plo5", nonFinite.get_non_finite() == 
              CBOR._bytes_to_uint(bytes.fromhex(hex[2:])))
  assert_false("plo6", nonFinite.get_sign() ^ (hex[2] == "f"))
  signedHex = hex[0:2] + "f" +hex[3:]
  nonFinite.set_sign(True)
  assert_true("plo7", nonFinite.get_sign())
  assert_true("plo8", nonFinite.encode().hex() == signedHex)
  nonFinite = CBOR.NonFinite.create_payload(payload).set_sign(False)
  assert_true("plo9", nonFinite.encode().hex() == hex[0:2] + "7" +hex[3:])

def int2bytes(value):
  res = bytearray()
  while True:
      res += bytes([value & 0xff])
      value >>= 8
      if value == 0: break
  res.reverse()
  return res

def oneNonFiniteTurn(value, binexpect, textexpect):
  nonfinite = CBOR.NonFinite(value)
  text = nonfinite.to_string()
  returnValue = nonfinite.get_non_finite()
  returnValue64 = nonfinite.get_non_finite64()
  textdecode = CBOR.from_diagnostic(textexpect)
  cbor = nonfinite.encode()
  refcbor = bytes.fromhex(binexpect)
  hexbin = cbor.hex()
  assert_true("eq1", text == textexpect)
  assert_true("eq2", hexbin == binexpect)
  assert_true("eq3", returnValue == CBOR.decode(cbor).get_non_finite())
  assert_true("eq4", returnValue == textdecode.get_non_finite())
  assert_true("eq5", len(int2bytes(returnValue)) == nonfinite.length)
  assert_true("eq7", len(int2bytes(returnValue64)) == 8)
  assert_true("eq8", nonfinite.equals(CBOR.decode(cbor)))
  rawcbor = int2bytes(value)
  rawcbor = bytes([0xf9 + (len(rawcbor) >> 2)]) + rawcbor
  if len(rawcbor) > len(refcbor):
    try:
      CBOR.decode(rawcbor)
      fail("d1")
    except Exception as e:
      check_exception(e, "Non-deterministic")
  else:
    CBOR.decode(rawcbor)
  assert_true("d3", CBOR.init_decoder(io.BytesIO(rawcbor),
                    CBOR.LENIENT_NUMBER_DECODING,
                    1000).decode_with_options().equals(nonfinite))
  object = CBOR.decode(refcbor)
  if textexpect.find("NaN") >= 0 or textexpect.find("Infinity") >= 0:
    assert_true("d4", object.to_string() == textexpect)
    assert_true("d5", object.is_simple())
    assert_true("d6", (textexpect.find("Infinity") >= 0) ^ object.is_nan())
  else:
    try:
      object.get_extended_float64()
      fail("d7")
    except Exception as e:
      check_exception(e, "7e00")
    assert_false("d9", object.is_simple())

oneTurn("0.0",                      "f90000")
oneTurn("-0.0",                     "f98000")
oneTurn("NaN",                      "f97e00")
oneTurn("Infinity",                 "f97c00")
oneTurn("-Infinity",                "f9fc00")
oneTurn("0.0000610649585723877",    "fa38801000")
oneTurn("10.559998512268066",       "fa4128f5c1")
oneTurn("65472.0",                  "f97bfe")
oneTurn("65472.00390625",           "fa477fc001")
oneTurn("65503.0",                  "fa477fdf00")
oneTurn("65504.0",                  "f97bff")
oneTurn("65504.00000000001",        "fb40effc0000000001")
oneTurn("65504.00390625",           "fa477fe001")
oneTurn("65504.5",                  "fa477fe080")
oneTurn("65505.0",                  "fa477fe100")
oneTurn("131008.0",                 "fa47ffe000")
oneTurn("-5.960464477539062e-8",    "fbbe6fffffffffffff")
oneTurn("-5.960464477539063e-8",    "f98001")
oneTurn("-5.960464477539064e-8",    "fbbe70000000000001")
oneTurn("-5.960465188081798e-8",    "fab3800001")
oneTurn("-5.963374860584736e-8",    "fab3801000")
oneTurn("-5.966285243630409e-8",    "fab3802000")
oneTurn("-8.940696716308594e-8",    "fab3c00000")
oneTurn("-0.00006097555160522461",  "f983ff")
oneTurn("-0.000060975551605224616", "fbbf0ff80000000001")
oneTurn("-0.000060975555243203416", "fab87fc001")
oneTurn("0.00006103515625",         "f90400")
oneTurn("0.00006103515625005551",   "fb3f10000000001000")
oneTurn("1.4012984643248169e-45",   "fb369fffffffffffff")
oneTurn("1.401298464324817e-45",    "fa00000001")
oneTurn("1.4012984643248174e-45",   "fb36a0000000000001")
oneTurn("1.4012986313726115e-45",   "fb36a0000020000000")
oneTurn("1.1754942106924411e-38",   "fa007fffff")
oneTurn("3.4028234663852886e+38",   "fa7f7fffff")
oneTurn("3.402823466385289e+38",    "fb47efffffe0000001")
oneTurn("0.00006109476089477539",   "f90401")
oneTurn("7.52316384526264e-37",     "fa03800000")
oneTurn("1.1754943508222875e-38",   "fa00800000")
oneTurn("5.0e-324",                 "fb0000000000000001")
oneTurn("-1.7976931348623157e+308", "fbffefffffffffffff")

oneNonFiniteTurn(0x7e00,             "f97e00",             "NaN")
oneNonFiniteTurn(0x7c01,             "f97c01",             "float'7c01'")
oneNonFiniteTurn(0xfc01,             "f9fc01",             "float'fc01'")
oneNonFiniteTurn(0x7fff,             "f97fff",             "float'7fff'")
oneNonFiniteTurn(0xfe00,             "f9fe00",             "float'fe00'")
oneNonFiniteTurn(0x7c00,             "f97c00",             "Infinity")
oneNonFiniteTurn(0xfc00,             "f9fc00",             "-Infinity")

oneNonFiniteTurn(0x7fc00000,         "f97e00",             "NaN")
oneNonFiniteTurn(0x7f800001,         "fa7f800001",         "float'7f800001'")
oneNonFiniteTurn(0xff800001,         "faff800001",         "float'ff800001'")
oneNonFiniteTurn(0x7fffffff,         "fa7fffffff",         "float'7fffffff'")
oneNonFiniteTurn(0xffc00000,         "f9fe00",             "float'fe00'")
oneNonFiniteTurn(0x7f800000,         "f97c00",             "Infinity")
oneNonFiniteTurn(0xff800000,         "f9fc00",             "-Infinity")

oneNonFiniteTurn(0x7ff8000000000000, "f97e00",             "NaN")
oneNonFiniteTurn(0x7ff0000000000001, "fb7ff0000000000001", "float'7ff0000000000001'")
oneNonFiniteTurn(0xfff0000000000001, "fbfff0000000000001", "float'fff0000000000001'")
oneNonFiniteTurn(0x7fffffffffffffff, "fb7fffffffffffffff", "float'7fffffffffffffff'")
oneNonFiniteTurn(0x7ff0000020000000, "fa7f800001",         "float'7f800001'")
oneNonFiniteTurn(0xfff0000020000000, "faff800001",         "float'ff800001'")
oneNonFiniteTurn(0xfff8000000000000, "f9fe00",             "float'fe00'")
oneNonFiniteTurn(0x7ff0040000000000, "f97c01",             "float'7c01'")
oneNonFiniteTurn(0x7ff0000000000000, "f97c00",             "Infinity")
oneNonFiniteTurn(0xfff0000000000000, "f9fc00",             "-Infinity")

nonFinite = CBOR.Float.create_extended_float(math.nan)
assert_true("conv", isinstance(nonFinite, CBOR.NonFinite))
assert_true("truncated", nonFinite.get_non_finite64() == 0x7ff8000000000000)  # Returns "quiet" NaN
assert_true("cbor", nonFinite.encode().hex() == "f97e00")                     # Encoded as it should
assert_true("combined", math.isnan(nonFinite.get_extended_float64()))         # Returns "Number"
assert_true("nan", nonFinite.is_nan())                                        # Indeed it is

payloadOneTurn(0,             "f97c00",              "Infinity")
payloadOneTurn(1,             "f97e00",                   "NaN")
payloadOneTurn(2,             "f97d00",                    None)
payloadOneTurn((1 << 10) - 1, "f97fff",                    None)
payloadOneTurn(1 << 10,       "fa7f801000",                None)
payloadOneTurn((1 << 23) - 1, "fa7fffffff",                None)
payloadOneTurn(1 << 23,       "fb7ff0000010000000",        None)
payloadOneTurn((1 << 52) - 1, "fb7fffffffffffffff",        None)
payloadOneTurn(1 << 52,       "f9fc00",             "-Infinity")
payloadOneTurn((1 << 52) + 1, "f9fe00",                    None)

for payload in [-1, 1 << 53]:
  try:
    CBOR.NonFinite.create_payload(payload).encode()
    fail("pl8")
  except Exception as e:
    check_exception(e, "Payload out of range")

def reducedOneTurn(f16, length, value, result):
  if isinstance(value, int): value = float(value)
  if isinstance(result, int): result = float(result)
  ok = length != None
  try:
    reduced = CBOR.Float.create_float16(value) if f16 else CBOR.Float.create_float32(value)
    assert_true("Should not", ok)
    assert_true("Compare", reduced.get_float64() == result)
    assert_true("len", reduced.length == length)
    assert_true("equi", CBOR.decode(reduced.encode()).equals(reduced))
##    console.log("Hi=" + result + " j=" + reduced + " l=" + reduced.length)
  except Exception as e:
#    console.log("EHi=" + result + " r=" + reduced + " v=" + value)
#    console.log(error.toString())
    assert_false("should" + repr(e), ok)
    check_exception(e, "Not possible reducing" if math.isfinite(value) else "NaN/")

reducedOneTurn(True, None, math.nan,                                0)
reducedOneTurn(True, 2,    60000,                               60000)
reducedOneTurn(True, 2,    5.960464477539063e-8, 5.960464477539063e-8)
reducedOneTurn(True, 2,    3.0e-8,               5.960464477539063e-8)
reducedOneTurn(True, 2,    2.0e-8,                                  0)
reducedOneTurn(True, 2,    65504.0,                           65504.0)
reducedOneTurn(True, 2,    65519.99,                          65504.0)
reducedOneTurn(True, 2,    -2.0e-9,                              -0.0)
reducedOneTurn(True, None, 65520,                             65504.0)
reducedOneTurn(True, 2,    10,                                     10)
reducedOneTurn(True, 2,    10.003906,                              10)
reducedOneTurn(True, 2,    10.003907,                      10.0078125)
reducedOneTurn(True, 2,    6.097555160522461e-5, 6.097555160522461e-5)
reducedOneTurn(True, 2,    6.097e-5,             6.097555160522461e-5)
reducedOneTurn(True, 2,    6.09e-5,              6.091594696044922e-5)

reducedOneTurn(False, None, math.nan, 0)
reducedOneTurn(False, 2, 2.5, 2.5)
reducedOneTurn(False, 2, 65504.0, 65504.0)
reducedOneTurn(False, 2, 5.960464477539063e-8, 5.960464477539063e-8)
reducedOneTurn(False, 4, 2.0e-8, 1.999999987845058e-8)
reducedOneTurn(False, 2, 5.960464477539063e-8, 5.960464477539063e-8)
reducedOneTurn(False, 4, 1.401298464324817e-45, 1.401298464324817e-45)
reducedOneTurn(False, 4, 3.4028234663852886e+38, 3.4028234663852886e+38)
reducedOneTurn(False, 4, 3.4028235e+38, 3.4028234663852886e+38)
reducedOneTurn(False, None, 3.40282358e+38, 3.4028234663852886e+38)


success()
"""],
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
except Exception as e:
  check_exception(e, "Expected 'int', got 'float'")

try:
  CBOR.Int("10")
  fail("Should not")
except Exception as e:
  check_exception(e, "Expected 'int', got 'str'")

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
    fail("Should fail")
  except Exception as error:
    check_exception(error, "Value out of range")
  test = 'CBOR.Int.create' + type + '(' + str(value) + ')'
  try:
    eval(test)
    fail("Should fail")
  except Exception as error:
    check_exception(error, "Value out of range")

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
['nondeterministic.py',
"""
# Testing "deterministic" code checks

def oneTurn(hex, dn):
  try:
    CBOR.decode(bytes.fromhex(hex))
    fail("Should fail on: " + dn)
  except Exception as error:
    check_exception(error, "Non-d")
  object = CBOR.init_decoder(io.BytesIO(bytes.fromhex(hex)), 
      CBOR.LENIENT_MAP_DECODING if dn.find("{") >= 0 else CBOR.LENIENT_NUMBER_DECODING, 100).decode_with_options()
  if (object.to_diagnostic(False) != dn or not object.equals(CBOR.decode(object.encode()))):
    fail("non match:" + dn)

oneTurn('1900ff', '255')
oneTurn('1817', '23')
oneTurn('A2026374776F01636F6E65', '{1:"one",2:"two"}')
oneTurn('FB7FF8000000000000', 'NaN')
oneTurn('FA7FC00000', 'NaN')
oneTurn('FB3ff0000000000000', '1.0')
oneTurn('c2480100000000000000', '72057594037927936')
oneTurn('c24900ffffffffffffffff', '18446744073709551615')
oneTurn('c240', '0')
oneTurn('c340', '-1')

# This one is actually deterministic...
try:
  oneTurn('fa7f7fffff', '3.4028234663852886e+38')
except Exception as error:
  check_exception(error, "Should fail on: ")

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
