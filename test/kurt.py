from org.webpki.cbor import CBOR

print(CBOR.NonFinite.create_payload(123456789).get_payload())