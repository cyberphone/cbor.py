# Testing "deterministic" code checks
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception
import io

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
