# Testing the "check_for_unread()" feature
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception

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
        "Map key 1 with argument of type=CBOR.String with value=\"hi\" was never read")

oneTurn("CBOR.Array().add(CBOR.Map().set(CBOR.Int(1), CBOR.String('hi')))",
        "res.get(0).get(CBOR.Int(1))",
        "Map key 1 with argument of type=CBOR.String with value=\"hi\" was never read")

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
        "Map key 1 with argument of type=CBOR.String with value=\"hi\" was never read")

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
oneTurn("CBOR.Tag(0, CBOR.String(\"2025-02-20T14:09:08Z\"))",
        "res.get()",
        "Tagged object 0 of type=CBOR.String with value=\"2025-02-20T14:09:08Z\" was never read")

oneTurn("CBOR.Tag(0, CBOR.String(\"2025-02-20T14:09:08Z\"))",
        "res.get().get_string()",
        None)

oneTurn("CBOR.Tag(8, CBOR.Int(2))",
        "res.get()",
        "Tagged object 8 of type=CBOR.Int with value=2 was never read")  

oneTurn("CBOR.Int(1)",
        "res.get_int32()",
        None)

success()
