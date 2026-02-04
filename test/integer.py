# Test program for integer "edge cases"
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success

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
  # assert_true("Failed decoding: " + value, CBOR.decode(cbor).get_integer() == value)
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

"""
try {
  CBOR.Int(1.1)
  fail("Should not")
} catch (error) {
  assert_true("msg1", error.toString().includes("Invalid integer: 1.1"))
}
try {
  CBOR.Int(Number.MAX_SAFE_INTEGER + 1)
  fail("Should not")
} catch (error) {
  assert_true("msg1", error.toString().includes("Invalid integer: " + (Number.MAX_SAFE_INTEGER + 1)))
}
try {
  CBOR.Int("10")
  fail("Should not")
} catch (error) {
  assert_true("msg2", error.toString().includes("Argument is not a 'number'"))
}
try {
  CBOR.Int(1, 7)
  fail("Should not")
} catch (error) {
  assert_true("msg4", error.toString().includes("CBOR.Int expects 1 argument(s)"))
}
"""
success(__file__)

