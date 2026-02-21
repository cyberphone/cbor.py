# Application note: Combining CBOR and Large Files
This note shows how you can combine CBOR with large files without embedding the files in CBOR.  The primary goal is to use as little RAM as possible.

The sample builds on using a CBOR sequence permitting succeeding data to be non-CBOR as outlined in 
[CBOR::Core](https://www.ietf.org/archive/id/draft-rundgren-cbor-core-25.html).

CBOR file in diagnostic notation:
```cbor
# Minimalist document metadata
{
  "file": "shanty-the-cat.jpg",
  "sha256": h'08d1440f4bf1e12b6e6815eaa636a573f1cac6d046a8bd517c32e22b6df0ec96'
}
```
Encoded, this is furnished in the file `metadata.cbor`

The concatnation of `metadata.cbor` and `shanty-the-cat.jpg` is subsequently stored in a file called `payload.bin`:
```
|--------------------|
|   CBOR meta-data   |
|--------------------|
|   attached file    |
|--------------------|
```

The sample code below shows how `payload.bin` could be processed by a receiver:
```python
# largefile.py

from org.webpki.cbor import CBOR
from cryptography.hazmat.primitives import hashes
import http.client

FILE_KEY = CBOR.String("file")
SHA256_KEY = CBOR.String("sha256")
CBOR_MAX_LENGTH = 1000
CHUNK_SIZE = 1000

# Initiate the hash method
digest = hashes.Hash(hashes.SHA256())

# Perform an HTTP request
conn = http.client.HTTPSConnection("cyberphone.github.io")
conn.request("GET", "/CBOR.py/doc/app-notes/large-payloads/payload.bin")
response = conn.getresponse()

# Show the response status
print(response.status, response.reason)

# Decode CBOR using the received stream handle
decoder = CBOR.init_decoder(response, CBOR.SEQUENCE_MODE, CBOR_MAX_LENGTH)
metadata = decoder.decode_with_options()

# Print CBOR object
print(metadata)
print("CBOR bytes: " + str(decoder.get_byte_count()))

# The rest of the stream is supposed to be the file.
# Read data in moderately-sized chunks.
total_bytes = 0
while True:
    chunk = response.read(CHUNK_SIZE)
    if chunk:
        # Hash the chunk.
        digest.update(chunk)
        total_bytes += len(chunk)
        ###################################################
        # Store the chunk in an application-specific way. #
        ###################################################
    else: break
if digest.finalize() != metadata.get(SHA256_KEY).get_bytes():
    print("Failed at SHA256")
else:
    print("Succesfully received: {:s} ({:n}))"
          .format(metadata.get(FILE_KEY).get_string(), total_bytes))
```
If all is good the result should be:
```
Successfully received: shanty-the-cat.jpg (2239423)
```

## Other solutions
Server-based attachments may also be provided as URLs.
