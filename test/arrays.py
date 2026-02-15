# Testing array operations
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception


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
