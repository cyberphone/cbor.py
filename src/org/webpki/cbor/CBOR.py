import binascii, struct, math

class CBOR:

  _MT_UNSIGNED     = 0x00
  _MT_NEGATIVE     = 0x20
  _MT_BYTES        = 0x40
  _MT_STRING       = 0x60
  _MT_ARRAY        = 0x80
  _MT_MAP          = 0xa0
  _MT_SIMPLE       = 0xe0
  _MT_TAG          = 0xc0
  _MT_BIG_UNSIGNED = 0xc2
  _MT_BIG_NEGATIVE = 0xc3
  _MT_FALSE        = 0xf4
  _MT_TRUE         = 0xf5
  _MT_NULL         = 0xf6
  _MT_FLOAT16      = 0xf9
  _MT_FLOAT32      = 0xfa
  _MT_FLOAT64      = 0xfb

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
    return bytearray([CBOR._MT_BIG_UNSIGNED if neg == 0 
                      else CBOR._MT_BIG_NEGATIVE]) + CBOR._encode_string(CBOR._MT_BYTES, array)

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

  class CborObject:
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

  ############
  #   Int    #
  ############
  class Int(CborObject):
    def __init__(self, value):
      super().__init__()
      self.value = CBOR._check_int_argument(value)

    def _internal_encode(self):
      return CBOR._encode_integer(CBOR._MT_UNSIGNED, self.value)
    
    def _get(self):
      return self.value
  
  ############
  #  Float   #
  ############
  class Float(CborObject):
    def __init__(self, value):
      super().__init__()
      if type(value).__name__ == 'int':
        value = float(value)
      self.value = CBOR._check_argument_type(value, 'float')
      u8 = bytearray(struct.pack('!d', value))
      print(binascii.hexlify(u8))
      if math.isfinite(value) == False:
        CBOR._error("NF Not implemented")
      if value == 0:
        CBOR._error("0 Not implemented")

    def _internal_encode(self):
      return CBOR._encode_integer(0x00, 5)
    
    def _get(self):
      return self.value
  
  ############
  #  String  #
  ############
  class String(CborObject):
    def __init__(self, string):
      super().__init__()
      self.string = CBOR._check_argument_type(string, 'str')

    def _internal_encode(self):
      return CBOR._encode_string(CBOR._MT_STRING, self.string.encode("utf8"))
  
    def _get(self):
      return self.string
    
  ############
  #  Array   #
  ############
  class Array(CborObject):
    def __init__(self):
      super().__init__()
      self.objects = list()

    def _internal_encode(self):
      encoded = CBOR._encode_integer(CBOR._MT_ARRAY, len(self.objects))
      for object in self.objects:
        encoded += object._internal_encode()
      return encoded
    
    def add(self, object):
      self.objects.append(object)
      return self
  
  @classmethod
  def decode(cls, cbor):
    print(cbor)

i = CBOR.Int(50)
print(binascii.hexlify(i.encode()))

print(i.get_int8())

s = CBOR.String("kurt€")
print(binascii.hexlify(s.encode()))

print(s.get_int8())

a = CBOR.Array()
a.add(i).add(s)
print(binascii.hexlify(a.encode()))

f = CBOR.Float(2.0e50)
print(f.get_float64())
print(binascii.hexlify(f.encode()))

CBOR.decode("DEC")
