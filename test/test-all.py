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
['maps.py',
"""
# Testing map operations

map = CBOR.Map().set(CBOR.Int(3), 
                     CBOR.String("three")).set(CBOR.Int(4), 
                                               CBOR.String("four"))
assert_true("size-0", map.length == 2)
keys = map.get_keys()
assert_true("size-1", len(keys) == 2)
assert_true("get-0", map.get(keys[0]).get_string() == "three")
assert_true("get-1", map.get(keys[1]).get_string() == "four")

assert_true("rem-0", map.remove(CBOR.Int(4)).get_string() == "four")
assert_true("size-2", map.length == 1)
assert_true("avail-0", map.contains_key(CBOR.Int(3)))
assert_false("avail-1", map.contains_key(CBOR.Int(4)))
assert_true("cond-0", map.get_conditionally(CBOR.Int(3), CBOR.String("k3")).get_string() == "three")
assert_true("cond-1", map.get_conditionally(CBOR.Int(4), CBOR.String("k4")).get_string() == "k4")
map = map.merge(
    CBOR.Map().set(CBOR.Int(1), CBOR.String("hi")).set(CBOR.Int(5), CBOR.String("yeah")))
assert_true("size-3", map.length == 3)
assert_true("merge-0", map.get(CBOR.Int(1)).get_string() == "hi")
assert_true("upd-0", map.update(CBOR.Int(1), CBOR.Int(-8), True).get_string() == "hi")
assert_true("upd-1", map.get(CBOR.Int(1)).get_bigint() == -8)
assert_true("upd-2", map.update(CBOR.Int(10), CBOR.Int(-8), False) == None)
assert_true("upd-3", map.get(CBOR.Int(10)).get_bigint() == -8)

def badKey(py):
  try:
    eval(py)
    fail("Must fail!")
  except Exception as e:
    check_exception(e, 'Map key')

immutableKey1 = CBOR.Array()
immutableKey2 = CBOR.Array()
CBOR.Map().set(immutableKey1, CBOR.Int(4))
badKey("immutableKey1.add(CBOR.Int(6))")
mutableValue = CBOR.Array()
CBOR.Map().set(CBOR.Int(5), mutableValue)
mutableValue.add(CBOR.Map())
CBOR.Map().set(CBOR.Array().add(immutableKey2), CBOR.Int(5))
badKey("immutableKey2.add(CBOR.Int(6))")

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
#    console.log(error.to_string())
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
  assert_true("Failed decoding: " + str(value), CBOR.decode(cbor).get_bigint() == value)
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
['diagnostic.py',
"""
# Testing "diagnostic notation"

def oneTurn(cbor_text, ok, compareWithOrNull):
  try:
    compare_text = compareWithOrNull if compareWithOrNull else cbor_text
    result = CBOR.from_diagnostic(cbor_text)
    assert_true("Should not", ok)
    sequence = CBOR.from_diagnostic_seq(cbor_text)
    if result.to_string() != compare_text:
      fail("input:\\n" + cbor_text + "\\nresult:\\n" + result.to_string())
    assert_true("seq", len(sequence) == 1)
    if sequence[0].to_string() != compare_text:
      fail("input:\\n" + cbor_text + "\\nresult:\\n" + result.to_string())
  except Exception as e:
    assert_false("Err: " + repr(e), ok)

def oneBinaryTurn(diag, hex):
  assert_true("bin", CBOR.from_diagnostic(diag).encode().hex() == hex)

oneTurn("2", True,  None)
oneTurn("2.0", True,  None)
oneTurn("123456789012345678901234567890", True,  None)
oneTurn("Infinity", True,  None)
oneTurn("-Infinity", True,  None)
oneTurn("NaN", True,  None)
oneTurn("0.0", True,  None)
oneTurn("-0.0", True,  None)
oneTurn('{\\n  4: "hi"\\n}', True,  None)
oneTurn('[4, true, false, null]', True,  None)
oneTurn('"next\\nline\\r\\\\\\ncont\\r\\nk"', True, '"next\\\\nline\\\\ncont\\\\nk"')
oneTurn('{1:<<  5   ,   7   >>}', True, "{\\n  1: h'0507'\\n}")
oneTurn('<<[3.0]>>', True, "h'81f94200'")
oneTurn('0b100_000000001', True, "2049")
oneTurn('4.0e+500', False,  None)
oneTurn('4.0e+5', True, "400000.0")
oneTurn('"missing', False,  None)
oneTurn('simple(21)', True, 'true')
oneTurn('simple(59)', True, 'simple(59)')
oneBinaryTurn('"\\\\ud800\\\\udd51"', "64f0908591")
oneBinaryTurn("'\\\\u20ac'", "43e282ac")
oneBinaryTurn('"\\\\"\\\\\\\\\\\\b\\\\f\\\\n\\\\r\\\\t"', "67225c080c0a0d09")

cborObject = CBOR.decode(bytes.fromhex('a20169746578740a6e6578740284fa3380000147a10564646\\
17461a1f5f4c074323032332d30362d30325430373a35333a31395a'))

cbor_text = ('{\\n' +
'  1: "text\\\\nnext",\\n' +
'  2: [\\n' +
# Note: Python does not use the JavaScript formatter which suppresses leading zeros. 
# Changed the text accordingly.
'    5.960465188081798e-08,\\n' +
'    h\\'a1056464617461\\',\\n' +
'    {\\n' +
'      true: false\\n' +
'    },\\n' +
'    0("2023-06-02T07:53:19Z")\\n' +
'  ]\\n' +
'}')

assert_true("pretty", cborObject.to_diagnostic(True) == cbor_text)
assert_true("oneline", cborObject.to_diagnostic(False) == 
                   cbor_text.replace('\\n', '').replace(' ',''))
assert_true("parse", CBOR.from_diagnostic(cbor_text).equals(cborObject))
sequence = CBOR.from_diagnostic_seq('45,{4:7}')
assert_true("seq2", len(sequence) == 2)
assert_true("seq3", sequence[0].get_int32() == 45)
assert_true("seq4", sequence[1].equals(CBOR.Map().set(CBOR.Int(4),CBOR.Int(7))))

try:
  CBOR.from_diagnostic("float'000000'")
  fail("bugf")
except Exception as e:
  check_exception(e, 'Argument must be a 16, 32, or 64-bit floating')

success()
"""],
['check-for-unread.py',
"""
# Testing the "check_for_unread()" feature

def oneTurn(create, access, error_string):
  res = eval(create)
  try:
    res.check_for_unread()
    if error_string is not None:
      fail("no way")    
  except Exception as e:
    check_exception(e, 'never read')
  try:
    eval(access)
    res.check_for_unread()
    assert_false("cfu1", error_string)
  except Exception as e:
    assert_true("cfu2", error_string)
    check_exception(e, error_string)
  eval(create).scan().check_for_unread()

oneTurn("CBOR.Array().add(CBOR.Map().set(CBOR.Int(1), CBOR.String('hi')))",
        "res.get(0).get(CBOR.Int(1)).get_string()",
        None)

oneTurn("CBOR.Array().add(CBOR.Map().set(CBOR.Int(1), CBOR.String('hi')))",
        "res",
        "Map key 1 with argument of type=CBOR.String with value=\\"hi\\" was never read")

oneTurn("CBOR.Array().add(CBOR.Map().set(CBOR.Int(1), CBOR.String('hi')))",
        "res.get(0).get(CBOR.Int(1))",
        "Map key 1 with argument of type=CBOR.String with value=\\"hi\\" was never read")

oneTurn("CBOR.Array().add(CBOR.Map())",
        "res",
        "Array element of type=CBOR.Map with value={} was never read")

# Empty Map => nothing to read
oneTurn("CBOR.Array().add(CBOR.Map())",
        "res.get(0)",
        "Array element of type=CBOR.Map with value={} was never read")

oneTurn("CBOR.Array().add(CBOR.Map())",
        "res.get(0).scan()",
        None)

# Empty Array => nothing to read
oneTurn("CBOR.Array()",
        "res",
        "Data of type=CBOR.Array with value=[] was never read")

oneTurn("CBOR.Array()",
        "res.scan()",
        None)

oneTurn("CBOR.Tag(8, CBOR.Map().set(CBOR.Int(1), CBOR.String('hi')))",
        "res.get().get(CBOR.Int(1)).get_string()",
        None)

oneTurn("CBOR.Tag(8, CBOR.Map().set(CBOR.Int(1), CBOR.String('hi')))",
        "res.get()",
        "Map key 1 with argument of type=CBOR.String with value=\\"hi\\" was never read")

oneTurn("CBOR.Tag(8, CBOR.Map())",
        "res.get()",
        "Tagged object 8 of type=CBOR.Map with value={} was never read")

oneTurn("CBOR.Simple(8)",
        "res",
        "Data of type=CBOR.Simple with value=simple(8) was never read")

oneTurn("CBOR.Simple(8)",
        "res.get_simple()",
        None)

oneTurn("CBOR.Tag(8, CBOR.Map())",
        "res.get().scan()",
        None)

# Date time specials
oneTurn("CBOR.Tag(0, CBOR.String(\\"2025-02-20T14:09:08Z\\"))",
        "res.get()",
        "Tagged object 0 of type=CBOR.String with value=\\"2025-02-20T14:09:08Z\\" was never read")

oneTurn("CBOR.Tag(0, CBOR.String(\\"2025-02-20T14:09:08Z\\"))",
        "res.get().get_string()",
        None)

oneTurn("CBOR.Tag(8, CBOR.Int(2))",
        "res.get()",
        "Tagged object 8 of type=CBOR.Int with value=2 was never read")  

oneTurn("CBOR.Int(1)",
        "res.get_int32()",
        None)

success()
"""],
['sequence.py',
"""
# Testing the "sequence" option

cbor = bytes([0x05, 0xa1, 0x05, 0x42, 0x6a, 0x6a])
try:
  CBOR.decode(cbor)
  fail("Should not")
except Exception as e:
  check_exception(e, 'Unexpected')
decoder = CBOR.init_decoder(io.BytesIO(cbor), CBOR.SEQUENCE_MODE, 10000)
total = bytearray()
while True:
  object = decoder.decode_with_options()
  if object is None: break
  total += object.encode()
assert_true("Comp", total == cbor)
assert_true("Comp2", len(total) == decoder.get_byte_count())
decoder = CBOR.init_decoder(io.BytesIO(bytes()), CBOR.SEQUENCE_MODE, 10000)
assert_true("Comp3", decoder.decode_with_options() == None)
assert_true("Comp4", decoder.get_byte_count() == 0)
array_sequence = CBOR.Array()
decoder = CBOR.init_decoder(io.BytesIO(cbor), CBOR.SEQUENCE_MODE, 10000)
while True:
  object = decoder.decode_with_options()
  if object is None: break
  array_sequence.add(object)
assert_true("Comp5", array_sequence.encode_as_sequence() == cbor)

success()
"""],
['clone.py',
"""
# Testing the "clone()" and "equals() methods

object = CBOR.Map().set(CBOR.Int(2), CBOR.Array().add(CBOR.Boolean(False)))
assert_true("clone+equals", object.equals(object.clone()))
copy = object.clone().set(CBOR.Int(1), CBOR.String("Hi"))
assert_false("copy+equals+clone", copy.equals(object))

success()
"""],
['cotx.py',
"""
# Testing the COTX identifier

def oneTurn(hex, dn, ok):
  try:
    object = CBOR.decode(bytes.fromhex(hex))
    assert_true("Should not execute", ok)
    if (object.to_string() != dn or not object.equals(CBOR.decode(object.encode()))):
      fail("non match:" + dn + " " + object.to_string())
  except Exception as e:
    if ok: print(repr(e))
    assert_false("Must succeed", ok)

oneTurn('d903f2623737', '1010("77")', False)
oneTurn('d903f281623737', '1010(["77"])', False)
oneTurn('d903f28206623737', '1010([6, "77"])', False)
oneTurn('d903f28262373707', '1010(["77", 7])', True)

success()
"""],
['miscellaneous.py',
"""
# miscellaneous tests

bin = bytes([0xa5, 0x01, 0xd9, 0x01, 0xf4, 0x81, 0x18, 0x2d, 0x02, 0xf9, 0x80, 0x10,
             0x04, 0x64, 0x53, 0x75, 0x72, 0x65, 0x05, 0xa2, 0x08, 0x69, 0x59, 0x65,
             0x0a, 0x01, 0x61, 0x68, 0xe2, 0x82, 0xac, 0x09, 0x85, 0x66, 0x42, 0x79,
             0x74, 0x65, 0x73, 0x21, 0x45, 0x01, 0x02, 0x03, 0x04, 0x05, 0xf5, 0xf4,
             0xf6, 0x06, 0xc2, 0x4b, 0x66, 0x1e, 0xfd, 0xf2, 0xe3, 0xb1, 0x9f, 0x7c, 
             0x04, 0x5f, 0x15])

cbor = CBOR.Map().set(CBOR.Int(5),
        CBOR.Map()
            .set(CBOR.Int(8), CBOR.String("Ye\\n\\u0001ah€"))
            .set(CBOR.Int(9),
                    CBOR.Array()
                        .add(CBOR.String("Bytes!"))
                        .add(CBOR.Bytes(bytes([1,2,3,4,5])))
                        .add(CBOR.Boolean(True))
                        .add(CBOR.Boolean(False))
                        .add(CBOR.Null()))).set(CBOR.Int(4), 
                CBOR.String("Sure")).set(CBOR.Int(2),
                CBOR.Float(-9.5367431640625e-7)).set(CBOR.Int(6),
                CBOR.Int(123456789123456789123456789)).set(CBOR.Int(1), 
                CBOR.Tag(500, CBOR.Array().add(CBOR.Int(45)))).encode()
assert_true("cmp1", bin == cbor)
array = CBOR.decode(cbor).get(CBOR.Int(5)).get(CBOR.Int(9))
assert_true("bool1", array.get(2).get_boolean())
assert_false("bool1", array.get(3).get_boolean())
assert_false("null1", array.get(3).is_null())
assert_true("null2", array.get(4).is_null())
assert_true("cmp2", CBOR.from_diagnostic(CBOR.decode(cbor).to_string()).encode() == bin)

assert_true("version", CBOR.version == "1.0.0")

success()
"""],
['nesting.py',
"""
# Testing nesting checking

def nest(setMax, level, ok):
  cborArray = CBOR.Array()
  lastArray = cborArray
  while True:
    level -= 1
    if level <= 0: break
    lastArray.add(lastArray := CBOR.Array())
  try:
    cborDecoder = CBOR.init_decoder(io.BytesIO(cborArray.encode()), 0, 10000)
    if setMax:
      cborDecoder.set_max_nesting_level(setMax)
    cborDecoder.decode_with_options()
    assert_true("mustnot", ok)
  except Exception:
#    console.log(error.to_string())
    assert_false("bad", ok)

nest(None, 100, True)
nest(None, 101, False)
nest(2, 2, True)
nest(2, 3, False)

success()
"""],
['base64url.py',
"""
# Testing the B64U/B64 converters

bin = bytearray(256)
for i in range(len(bin)):
  bin[i] = i

# This is what "btoa" returns for bin:
b64 = 'AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissL\\
S4vMDEyMzQ1Njc4OTo7PD0+P0BBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWltcXV5fYGFiY\\
2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6e3x9fn+AgYKDhIWGh4iJiouMjY6PkJGSk5SVlpeYm\\
ZqbnJ2en6ChoqOkpaanqKmqq6ytrq+wsbKztLW2t7i5uru8vb6/wMHCw8TFxsfIycrLzM3Oz\\
9DR0tPU1dbX2Nna29zd3t/g4eLj5OXm5+jp6uvs7e7v8PHy8/T19vf4+fr7/P3+/w=='

# Base64Url decoding is "permissive" and takes Base64 with padding as well...
bin2 = CBOR.from_diagnostic("b64'" + b64 + "'").get_bytes()
assert_true("cmp2", bin == bin2)

assert_true("cmp3", CBOR.from_diagnostic("b64'oQVkZGF0YQ'") ==
                    CBOR.from_diagnostic("h'a1056464617461'"))
# Zero data is compliant
assert_true("cmp4", CBOR.from_diagnostic("b64''").get_bytes() == bytes())
assert_true("cmp4", CBOR.decode(bytes([0x60])).get_string() == "")

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
    return self._greeting

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
