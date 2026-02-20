# Testing the B64U/B64 converters
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception

bin = bytearray(256)
for i in range(len(bin)):
  bin[i] = i

# This is what "btoa" returns for bin:
b64 = 'AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissL\
S4vMDEyMzQ1Njc4OTo7PD0+P0BBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWltcXV5fYGFiY\
2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6e3x9fn+AgYKDhIWGh4iJiouMjY6PkJGSk5SVlpeYm\
ZqbnJ2en6ChoqOkpaanqKmqq6ytrq+wsbKztLW2t7i5uru8vb6/wMHCw8TFxsfIycrLzM3Oz\
9DR0tPU1dbX2Nna29zd3t/g4eLj5OXm5+jp6uvs7e7v8PHy8/T19vf4+fr7/P3+/w=='

# Base64Url decoding is "permissive" and takes Base64 with padding as well...
bin2 = CBOR.from_diagnostic("b64'" + b64 + "'").get_bytes()
assert_true("cmp2", bin == bin2)

assert_true("cmp3", CBOR.from_diagnostic("b64'oQVkZGF0YQ'") ==
                    CBOR.from_diagnostic("h'a1056464617461'"))
# Zero data is compliant
assert_true("cmp4", CBOR.from_diagnostic("b64''").get_bytes() == bytes())
assert_true("cmp4", CBOR.decode(bytes([0x60])).get_string() == "")

success()
