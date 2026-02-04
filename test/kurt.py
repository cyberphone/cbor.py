from org.webpki.cbor import CBOR
import binascii


##########################
#       Testing...       #
##########################

i = CBOR.Int(50)
print(binascii.hexlify(i.encode()))

print(i.get_int8())

s = CBOR.String("kurt€")
print(binascii.hexlify(s.encode()))

# print(s.get_int8())

a = CBOR.Array()
a.add(i).add(s)
print(binascii.hexlify(a.encode()))

f = CBOR.Float(2.0e50)
print(f.get_float64())
print(binascii.hexlify(f.encode()))

print(binascii.hexlify(CBOR.Bytes(bytes([0,1,0x99])).encode()))

k = CBOR.Int(7)
k.get_int8()
k.check_for_unread()

CBOR.decode("DEC".encode("utf8"))

import http.client
conn = http.client.HTTPSConnection("cyberphone.github.io")
conn.request("GET", "/javaapi/app-notes/large-payloads/metadata.cbor")
response = conn.getresponse()
print(response.status, response.reason)
CBOR.init_decoder(response, 10000).decode_with_options()

print(binascii.hexlify(CBOR.NonFinite(0x7ff0000000000000).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload(0x1).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload((1 << 10) - 1).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload((1 << 23) - 1).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload(1 << 10).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload((1 << 52) - 1).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload((1 << 52) - 1).set_sign(True).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload((1 << 53) - 1).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload((1 << 52) + 1).encode()))
print(binascii.hexlify(CBOR.NonFinite.create_payload(1 << 23).encode()))

print(CBOR.NonFinite.create_payload(123456789).get_payload())

print(CBOR.NonFinite.create_payload(123456789).get_payload())