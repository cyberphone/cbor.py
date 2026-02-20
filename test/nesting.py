# Testing nesting checking
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception
import io

def nest(setMax, level, ok):
  cborArray = CBOR.Array()
  lastArray = cborArray
  while True:
    level -= 1
    if level <= 0: break
    lastArray.add(lastArray := CBOR.Array())
  try:
    cborDecoder = CBOR.init_decoder(io.BytesIO(cborArray.encode()), 0, 10000)
    if setMax:
      cborDecoder.set_max_nesting_level(setMax)
    cborDecoder.decode_with_options()
    assert_true("mustnot", ok)
  except Exception:
#    console.log(error.toString())
    assert_false("bad", ok)

nest(None, 100, True)
nest(None, 101, False)
nest(2, 2, True)
nest(2, 3, False)

success()
