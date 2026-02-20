# Testing the "clone()" and "equals() methods
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception

object = CBOR.Map().set(CBOR.Int(2), CBOR.Array().add(CBOR.Boolean(False)))
assert_true("clone+equals", object.equals(object.clone()))
copy = object.clone().set(CBOR.Int(1), CBOR.String("Hi"))
assert_false("copy+equals+clone", copy.equals(object))

success()
