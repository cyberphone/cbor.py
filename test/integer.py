# Test program for integer "edge cases"
import CBOR from org.webpki.cbor.cbor

function oneTurn(value, expected) {
  let text = value.toString();
  while (text.length < 25) {
    text += ' ';
  }
  let cbor = CBOR.Int(value).encode();
  let got = CBOR.toHex(cbor);
  if (got != expected) {
    got = '***=' + got;
  } else {
    got = '';
  }
  assertTrue("Failed decoding: " + value, CBOR.decode(cbor).getBigInt() == value);
  while (expected.length < 20) {
    expected += ' ';
  }
  if (got.length) {
    fail(text + expected + got);
  }
}
# -0 is treated as 0 for integers
assertTrue("minus-0", CBOR.toHex(CBOR.Int(-0).encode()) == "00");
oneTurn(0, '00');
oneTurn(-1, '20');
oneTurn(255, '18ff');
oneTurn(256, '190100');
oneTurn(-256, '38ff');
oneTurn(-257, '390100');
oneTurn(1099511627775, '1b000000ffffffffff');
oneTurn(18446744073709551615, '1bffffffffffffffff');
oneTurn(18446744073709551616, 'c249010000000000000000');
oneTurn(-18446744073709551616, '3bffffffffffffffff');
oneTurn(-18446744073709551617, 'c349010000000000000000');

try {
  CBOR.Int(1.1);
  fail("Should not");
} catch (error) {
  assertTrue("msg1", error.toString().includes("Invalid integer: 1.1"));
}
try {
  CBOR.Int(Number.MAX_SAFE_INTEGER + 1);
  fail("Should not");
} catch (error) {
  assertTrue("msg1", error.toString().includes("Invalid integer: " + (Number.MAX_SAFE_INTEGER + 1)));
}
try {
  CBOR.Int("10");
  fail("Should not");
} catch (error) {
  assertTrue("msg2", error.toString().includes("Argument is not a 'number'"));
}
try {
  CBOR.Int(1, 7);
  fail("Should not");
} catch (error) {
  assertTrue("msg4", error.toString().includes("CBOR.Int expects 1 argument(s)"));
}

success();
