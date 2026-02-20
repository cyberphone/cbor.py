# Testing the "sequence" option
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception
import io

cbor = bytes([0x05, 0xa1, 0x05, 0x42, 0x6a, 0x6a])
try:
  CBOR.decode(cbor)
  fail("Should not")
except Exception as e:
  check_exception(e, 'Unexpected')
decoder = CBOR.init_decoder(io.BytesIO(cbor), CBOR.SEQUENCE_MODE, 10000)
total = bytearray()
while True:
  object = decoder.decode_with_options()
  if object is None: break
  total += object.encode()
assert_true("Comp", total == cbor)
assert_true("Comp2", len(total) == decoder.get_byte_count())
decoder = CBOR.init_decoder(io.BytesIO(bytes()), CBOR.SEQUENCE_MODE, 10000)
assert_true("Comp3", decoder.decode_with_options() == None)
assert_true("Comp4", decoder.get_byte_count() == 0)
array_sequence = CBOR.Array()
decoder = CBOR.init_decoder(io.BytesIO(cbor), CBOR.SEQUENCE_MODE, 10000)
while True:
  object = decoder.decode_with_options()
  if object is None: break
  array_sequence.add(object)
assert_true("Comp5", array_sequence.encode_as_sequence() == cbor)

success()
