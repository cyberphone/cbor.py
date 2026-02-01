import binascii

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
    # True "BigInt".
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

    def getInteger(self):
      if type(self).__name__ != 'Int':
        raise CBOR.Exception("Expected: " + 'CBOR.Int' + 
                             "', got 'CBOR." + type(self).__name__  + "'")
      return self.value

    def getInt8(self):
      return CBOR.intRange(self.getInteger(), -128, 127)

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

  ############
  #  String  #
  ############
  class String(CborObject):
    def __init__(self, value):
      self.value = CBOR.checkType(value, 'str')

    def internalEncode(self):

      return self.value
    
  ############
  #  Array   #
  ############
  class Array(CborObject):
    def __init__(self):
      self.objects = list()

    def internalEncode(self):
      return len(self.objects)
    
    def add(self, object):
      self.objects.append(object)
      return self

i = CBOR.Int(50)
print(binascii.hexlify(i.encode()))

print(i.getInt8())

s = CBOR.String("kurt")
print(s.encode())

#print(s.getInt8())

a = CBOR.Array()
a.add(i).add(s)
print(a.encode())
