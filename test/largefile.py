from org.webpki.cbor import CBOR
from cryptography.hazmat.primitives import hashes
import http.client

conn = http.client.HTTPSConnection("cyberphone.github.io")
conn.request("GET", "/javaapi/app-notes/large-payloads/payload.bin")
response = conn.getresponse()
print(response.status, response.reason)
decoder = CBOR.init_decoder(response, CBOR.SEQUENCE_MODE, 10000)
metadata = decoder.decode_with_options()
print(metadata)
print("CBOR bytes: " + str(decoder.get_byte_count()))
digest = hashes.Hash(hashes.SHA256())
count = 0
while True:
    buffer = response.read(1000)
    if buffer:
        digest.update(buffer)
        count += len(buffer)
    else: break
if digest.finalize() != metadata.get(CBOR.String("sha256")).get_bytes():
    print("Failed at SHA256")
else:
    print("Succefully received file: {:s} ({:n}))"
          .format(metadata.get(CBOR.String('file')).get_string(), count))



