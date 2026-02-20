# The demo examples from README.md
from org.webpki.cbor import CBOR

###############################
#          Encoding           #
###############################
cbor = CBOR.Map()\
           .set(CBOR.Int(1), CBOR.Float(45.7))\
           .set(CBOR.Int(2), CBOR.String("Hi there!")).encode()

print(cbor.hex())

###############################
#          Decoding.          #
###############################
map = CBOR.decode(cbor)
print(map.to_string())  # Diagnostic notation

print('Value={:g}'.format(map.get(CBOR.Int(1)).get_float64()))

###############################
# Diagnostic notation parsing #
###############################
cbor = CBOR.from_diagnostic("""{
# Comments are also permitted
  1: 45.7,
  2: "Hi there!"
}""").encode()

print(cbor.hex())
