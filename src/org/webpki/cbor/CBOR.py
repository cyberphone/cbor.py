import binascii, struct, math

class CBOR:
  class Exception(Exception):
    def __init__(self, msg):
      self.msg = msg
      super().__init__(self.msg)

  @staticmethod
  def encodeString(tag, binary):
    return CBOR.encodeInteger(tag, len(binary)) + binary

  @staticmethod
  def encodeInteger(tag, value):
    neg = value < 0
    # Only applies to "int" and "bigint"
    if (neg):
      value = ~value
      tag = 0x20
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
    return bytearray([0xc2 if neg == 0 else 0xc3]) + CBOR.encodeString(0x40, array)

  @staticmethod
  def intRange(value, min, max):
    if (value < min or value > max):
      raise CBOR.Exception("Value out of range: " + str(value))
    return value

  @staticmethod
  def checkType(value, expected):
    if type(value).__name__ != expected:
      raise CBOR.Exception("Expected '" + expected + "', got '" + type(value).__name__ + "'")
    return value
    
  @staticmethod
  def checkInt(value):
    return CBOR.checkType(value, 'int')

  class CborObject:
    print("Hi")

    def checkAndGet(self, expected):
      if type(self).__name__ != expected:
        raise CBOR.Exception("Expected: '" + 'CBOR.' + expected +
                             "', got 'CBOR." + type(self).__name__  + "'")
      return self._get()

    def getInteger(self):
      return self.checkAndGet('Int')

    def getInt8(self):
      return CBOR.intRange(self.getInteger(), -128, 127)
    
    def getU128(self):
      return CBOR.intRange(self.getInteger(), 0, 0xffffffffffffffffffffffffffffffff)
    
    def getFloat64(self):
      return self.checkAndGet('Float')
    
    def getString(self):
      return self.checkAndGet('String')

    def encode(self):
      return self.internalEncode()

  ############
  #   Int    #
  ############
  class Int(CborObject):
    def __init__(self, value):
      self.value = CBOR.checkInt(value)

    def internalEncode(self):
      return CBOR.encodeInteger(0x00, self.value)
    
    def _get(self):
      return self.value
  
  ############
  #  Float   #
  ############
  class Float(CborObject):
    def __init__(self, value):
      if type(value).__name__ == 'int':
        value = float(value)
      self.value = CBOR.checkType(value, 'float')
      u8 = bytearray(struct.pack('!d', value))
      print(binascii.hexlify(u8))
      if math.isfinite(value) == False:
        raise CBOR.Exception("NF Not implemented")
      if value == 0:
        raise CBOR.Exception("0 Not implemented")

    def internalEncode(self):
      return CBOR.encodeInteger(0x00, 5)
    
    def _get(self):
      return self.value
  
  ############
  #  String  #
  ############
  class String(CborObject):
    def __init__(self, string):
      self.string = CBOR.checkType(string, 'str')

    def internalEncode(self):
      return CBOR.encodeString(0x60, self.string.encode("utf8"))
  
    def _get(self):
      return self.string
    
  ############
  #  Array   #
  ############
  class Array(CborObject):
    def __init__(self):
      self.objects = list()

    def internalEncode(self):
      encoded = CBOR.encodeInteger(0x80, len(self.objects))
      for object in self.objects:
        encoded += object.internalEncode()
      return encoded
    
    def add(self, object):
      self.objects.append(object)
      return self

i = CBOR.Int(50)
print(binascii.hexlify(i.encode()))

print(i.getInt8())

s = CBOR.String("kurt€")
print(binascii.hexlify(s.encode()))

#print(s.getInt8())

a = CBOR.Array()
a.add(i).add(s)
print(binascii.hexlify(a.encode()))

f = CBOR.Float(2.0e50)
print(f.getFloat64())
print(binascii.hexlify(f.encode()))
