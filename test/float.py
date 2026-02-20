# Test program for floating-point "edge cases"
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception
import math
import struct
import io

def overflow(decodedValue, length):
  test = 'decodedValue.get_float' + length + '()'
  try:
    eval(test)
    fail("Should fail")
  except Exception as e:
    check_exception(e, "Value out of range for \"float")

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
