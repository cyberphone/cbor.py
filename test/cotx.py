# Testing the COTX identifier
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception

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
