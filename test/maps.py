# Testing map operations
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception

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
