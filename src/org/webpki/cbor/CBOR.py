import binascii, struct, math, io

class CBOR:

  _MT_UNSIGNED      = 0x00
  _MT_NEGATIVE      = 0x20
  _MT_BYTES         = 0x40
  _MT_STRING        = 0x60
  _MT_ARRAY         = 0x80
  _MT_MAP           = 0xa0
  _MT_TAG           = 0xc0
  _MT_SIMPLE        = 0xe0

  _TAG_BIG_UNSIGNED = 0xc2
  _TAG_BIG_NEGATIVE = 0xc3

  _SIMPLE_FALSE     = 0xf4
  _SIMPLE_TRUE      = 0xf5
  _SIMPLE_NULL      = 0xf6
  _SIMPLE_FLOAT16   = 0xf9
  _SIMPLE_FLOAT32   = 0xfa
  _SIMPLE_FLOAT64   = 0xfb

  class Exception(Exception):
    def __init__(self, msg):
      super().__init__(msg)

  @staticmethod
  def _error(msg):
    raise CBOR.Exception(msg)

  @staticmethod
  def _encode_string(tag, binary):
    return CBOR._encode_integer(tag, len(binary)) + binary

  @staticmethod
  def _encode_integer(tag, value):
    neg = value < 0
    # Only applies to "int" and "bigint"
    if (neg):
      value = ~value
      tag = CBOR._MT_NEGATIVE
    # Convert int to bytearray (but with a twist).
    array = bytearray()
    while True:
      array += bytes([value & 0xff])
      value >>= 8
      if value == 0:
        break
    length = len(array)
    # Prepare for "int" encoding (1, 2, 4, 8).  Only 3, 5, 6, and 7 need an action.
    while length < 8 and length > 2 and length != 4:
      array += bytes([0])
      length += 1
    # Make big endian.
    array.reverse()
    # Does this number qualify as a "bigint"?
    if length <= 8:
      # Apparently not, encode it as "int".
      if length == 1 and array[0] <= 23:
        return bytearray([array[0] | tag])
      modifier = 24
      while True:
        length >>= 1
        if length == 0:
          break  
        modifier += 1
      return bytearray([tag | modifier]) + array
    # True "bigint".
    return bytearray([CBOR._TAG_BIG_UNSIGNED if neg == 0 
                      else CBOR._TAG_BIG_NEGATIVE]) + CBOR._encode_string(CBOR._MT_BYTES, array)

  @staticmethod
  def _int_range_check(value, min, max):
    if (value < min or value > max):
      CBOR._error("Value out of range: " + str(value))
    return value

  @staticmethod
  def _check_argument_type(value, expected):
    if type(value).__name__ != expected:
      CBOR._error("Expected '" + expected + "', got '" + type(value).__name__ + "'")
    return value
    
  @staticmethod
  def _check_int_argument(value):
    return CBOR._check_argument_type(value, 'int')

  class _CborObject:
    def __init__(self):
      self.readFlag = False

    def _check_type_get_value(self, expected):
      if type(self).__name__ != expected:
        CBOR._error("Expected '" + 'CBOR.' + expected +
                    "', got 'CBOR." + type(self).__name__  + "'")
      self.readFlag = True
      return self._get()

    def _get_integer(self):
      return self._check_type_get_value('Int')

    def get_int8(self):
      return CBOR._int_range_check(self._get_integer(), -128, 127)
    
    def get_uint128(self):
      return CBOR._int_range_check(self._get_integer(), 0, 0xffffffffffffffffffffffffffffffff)
    
    def get_float64(self):
      return self._check_type_get_value('Float')
    
    def get_string(self):
      return self._check_type_get_value('String')

    def encode(self):
      return self._internal_encode()
    
    def check_for_unread(self):
      if not self.readFlag:
        CBOR._error("Not read: " + type(self).__name__)

  ############
  #   Int    #
  ############
  class Int(_CborObject):
    def __init__(self, value):
      super().__init__()
      self._value = CBOR._check_int_argument(value)

    def _internal_encode(self):
      return CBOR._encode_integer(CBOR._MT_UNSIGNED, self._value)
    
    def _get(self):
      return self._value
  
  ############
  #  Float   #
  ############
  class Float(_CborObject):
    def __init__(self, value):
      super().__init__()
      if type(value).__name__ == 'int':
        value = float(value)
      self._value = CBOR._check_argument_type(value, 'float')
      u8 = bytearray(struct.pack('!d', value))
      print(binascii.hexlify(u8))
      if not math.isfinite(value):
        CBOR._error("NF Not implemented")
      if value == 0:
        CBOR._error("0 Not implemented")

    def _internal_encode(self):
      return CBOR._encode_integer(0x00, 5)
    
    def _get(self):
      return self._value
  
  ############
  #  String  #
  ############
  class String(_CborObject):
    def __init__(self, string):
      super().__init__()
      self._string = CBOR._check_argument_type(string, 'str')

    def _internal_encode(self):
      return CBOR._encode_string(CBOR._MT_STRING, self._string.encode("utf8"))
  
    def _get(self):
      return self._string
    
  ############
  #  Array   #
  ############
  class Array(_CborObject):
    def __init__(self):
      super().__init__()
      self._objects = list()

    def _internal_encode(self):
      encoded = CBOR._encode_integer(CBOR._MT_ARRAY, len(self._objects))
      for object in self._objects:
        encoded += object._internal_encode()
      return encoded
    
    def add(self, object):
      self._objects.append(object)
      return self

  ################  
  #   Decoding   #
  ################
  class _Decoder:
    def __init__(self, cbor_stream, max_length):
      CBOR._check_int_argument(max_length)
      if not isinstance(cbor_stream, io.BufferedIOBase):
        CBOR._error("Unexpected stream type: " + type(cbor_stream).__name__)
      self._cbor_stream = cbor_stream
      self._max_length = max_length
      self._current = 0
  
    def decode_with_options(self):
        while (chunk := self._cbor_stream.read(1)):
          self._current += 1
        print(str(self._current))

  @classmethod
  def decode(cls, cbor):
    if type(cbor).__name__ not in ['bytes', 'bytearray']:
      CBOR._error("Unexpected CBOR argument: " + type(cbor).__name__)
    CBOR.init_decoder(io.BytesIO(cbor), len(cbor)).decode_with_options()

  @classmethod
  def init_decoder(cls, cbor_stream, max_length):
    return CBOR._Decoder(cbor_stream, max_length)


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

k = CBOR.Int(7)
k.get_int8()
k.check_for_unread()

CBOR.decode("DEC".encode("utf8"))

import http.client
conn = http.client.HTTPSConnection("cyberphone.github.io")
conn.request("GET", "/javaapi/app-notes/large-payloads/metadata.cbor")
r1 = conn.getresponse()
print(r1.status, r1.reason)
CBOR.init_decoder(r1, 10000).decode_with_options()

