# Testing "diagnostic notation"
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception

def oneTurn(cbor_text, ok, compareWithOrNull):
  try:
    compare_text = compareWithOrNull if compareWithOrNull else cbor_text
    result = CBOR.from_diagnostic(cbor_text)
    assert_true("Should not", ok)
    sequence = CBOR.from_diagnostic_seq(cbor_text)
    if result.to_string() != compare_text:
      fail("input:\n" + cbor_text + "\nresult:\n" + result.to_string())
    assert_true("seq", len(sequence) == 1)
    if sequence[0].to_string() != compare_text:
      fail("input:\n" + cbor_text + "\nresult:\n" + result.to_string())
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
oneTurn('{\n  4: "hi"\n}', True,  None)
oneTurn('[4, true, false, null]', True,  None)
oneTurn('"next\nline\r\\\ncont\r\nk"', True, '"next\\nline\\ncont\\nk"')
oneTurn('{1:<<  5   ,   7   >>}', True, "{\n  1: h'0507'\n}")
oneTurn('<<[3.0]>>', True, "h'81f94200'")
oneTurn('0b100_000000001', True, "2049")
oneTurn('4.0e+500', False,  None)
oneTurn('4.0e+5', True, "400000.0")
oneTurn('"missing', False,  None)
oneTurn('simple(21)', True, 'true')
oneTurn('simple(59)', True, 'simple(59)')
oneBinaryTurn('"\\ud800\\udd51"', "64f0908591")
oneBinaryTurn("'\\u20ac'", "43e282ac")
oneBinaryTurn('"\\"\\\\\\b\\f\\n\\r\\t"', "67225c080c0a0d09")

cborObject = CBOR.decode(bytes.fromhex('a20169746578740a6e6578740284fa3380000147a10564646\
17461a1f5f4c074323032332d30362d30325430373a35333a31395a'))

cbor_text = ('{\n' +
'  1: "text\\nnext",\n' +
'  2: [\n' +
# Note: Python does not use the JavaScript formatter which suppresses leading zeros. 
# Changed the text accordingly.
'    5.960465188081798e-08,\n' +
'    h\'a1056464617461\',\n' +
'    {\n' +
'      true: false\n' +
'    },\n' +
'    0("2023-06-02T07:53:19Z")\n' +
'  ]\n' +
'}')

assert_true("pretty", cborObject.to_diagnostic(True) == cbor_text)
assert_true("oneline", cborObject.to_diagnostic(False) == 
                   cbor_text.replace('\n', '').replace(' ',''))
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
