################################################################
#                                                              #
#                 CBOR::Core API for Python3                   #
#                                                              #
# Author: Anders Rundgren (anders.rundgren.net@gmail.com)      #
# Repository: https://github.com/cyberphone/cbor.py.           #
#                                                              #
# Note: this is a "Reference Implementation", not optimized    #
# for maximum performance.  It is assumed that a productified  #
# version of cbor.py would be rewritten in C.                  #
################################################################

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

  def __init__(self):
    CBOR._error("Invalid operation")

  class Exception(Exception):
    def __init__(self, msg):
      super().__init__(msg)

  @staticmethod
  def _error(msg):
    raise CBOR.Exception(msg)

  @staticmethod
  def _encode_string(tag, binary):
    return CBOR._generic_header(tag, len(binary)) + binary

  @staticmethod
  def _generic_header(tag, value):
    # Convert unsigned integer to bytearray (but with a twist).
    array = bytearray()
    while True:
      array += bytes([value & 0xff])
      value >>= 8
      if value == 0: break
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
        if length == 0: break  
        modifier += 1
      return bytearray([tag | modifier]) + array
    # True "bigint".
    return bytearray([CBOR._TAG_BIG_UNSIGNED if tag == CBOR._MT_UNSIGNED 
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

  @staticmethod
  def _check_bytes_argument(byte_string):  
    if type(byte_string).__name__ not in ['bytes', 'bytearray']:
      CBOR._error("Unexpected CBOR argument: " + type(byte_string).__name__)
    return byte_string
  
  @staticmethod
  def _reverse_payload(b51b0):
    reversed = 0
    bit_count = 0
    while b51b0 > 0:
      bit_count += 1
      reversed <<= 1
      if (b51b0 & 1) == 1:
        reversed |= 1
      b51b0 >>= 1
    return reversed << (52 - bit_count)

  class _CborObject:
    def __init__(self):
      self.readFlag = False

    def _check_type_get_value(self, expected):
      if type(self).__name__ != expected:
        CBOR._error("Expected '" + 'CBOR.' + expected +
                    "', got 'CBOR." + type(self).__name__  + "'")
      self.readFlag = True
      return self._get()

    def  get_integer(self):
      return self._check_type_get_value('Int')

    def get_int8(self):
      return CBOR._int_range_check(self. get_integer(), -128, 127)
    
    def get_uint128(self):
      return CBOR._int_range_check(self. get_integer(), 0, 0xffffffffffffffffffffffffffffffff)
    
    def get_float64(self):
      return self._check_type_get_value('Float')
    
    def get_string(self):
      return self._check_type_get_value('String')
    
    def get_non_finite64(self):
      return self._check_type_get_value('NonFinite')

    def encode(self):
      return self._internal_encode()
    
    def check_for_unread(self):
      if not self.readFlag:
        CBOR._error("Not read: " + type(self).__name__)

  ##########################
  #       CBOR.Int         #
  ##########################
  class Int(_CborObject):
    def __init__(self, value):
      super().__init__()
      self._value = CBOR._check_int_argument(value)

    def _internal_encode(self):
      tag = CBOR._MT_UNSIGNED
      value = self._value
      if value < 0:
        tag = CBOR._MT_NEGATIVE
        value = ~value
      return CBOR._generic_header(tag, value)
    
    def _get(self):
      return self._value
  
  ##########################
  #       CBOR.Float       #
  ##########################
  class Float(_CborObject):
    def __init__(self, value):
      super().__init__()
      if type(value).__name__ == 'int':
        value = float(value)
      self._value = CBOR._check_argument_type(value, 'float')
      f64b = bytearray(struct.pack('!d', value))
      print(binascii.hexlify(f64b))
      if not math.isfinite(value):
        CBOR._error("Not permitted: 'NaN/Infinity'")
      if value == 0:
        CBOR._error("0 Not implemented")

    def _internal_encode(self):
      return CBOR._generic_header(0x00, 5)
    
    def _get(self):
      return self._value
  
  ##########################
  #      CBOR.String       #
  ##########################
  class String(_CborObject):
    def __init__(self, text_string):
      super().__init__()
      self._string = CBOR._check_argument_type(text_string, 'str')

    def _internal_encode(self):
      return CBOR._encode_string(CBOR._MT_STRING, self._string.encode("utf8"))
  
    def _get(self):
      return self._string
    
  ##########################
  #       CBOR.Bytes       #
  ##########################
  class Bytes(_CborObject):
    def __init__(self, byte_string):
      super().__init__()
      self._string = CBOR._check_bytes_argument(byte_string)

    def _internal_encode(self):
      return CBOR._encode_string(CBOR._MT_BYTES, self._string)
  
    def _get(self):
      return self._string
    
  ##########################
  #       CBOR.Array       #
  ##########################
  class Array(_CborObject):
    def __init__(self):
      super().__init__()
      self._objects = list()

    def _internal_encode(self):
      encoded = CBOR._generic_header(CBOR._MT_ARRAY, len(self._objects))
      for object in self._objects:
        encoded += object._internal_encode()
      return encoded
    
    def add(self, object):
      self._objects.append(object)
      return self

  ##########################
  #     CBOR.NonFinite     #
  ##########################
  class NonFinite(_CborObject):
    def __init__(self, value):
      super().__init__()
      self._original = CBOR._check_int_argument(value)
      self._create_det_enc(value)

    def _create_det_enc(self, value):
      while True:
        self._ieee754 = bytearray()
        i = value
        if i < 0: self._bad_value()
        while True:
          self._ieee754 += bytes([i & 0xff])
          i >>= 8
          if i == 0: break
        self._ieee754.reverse()
        match len(self._ieee754):
          case 2: exponent = 0x7c00
          case 4: exponent = 0x7f800000
          case 8: exponent = 0x7ff0000000000000
          case _: self._bad_value()
        sign = self._ieee754[0] > 0x7f
        if (value & exponent) != exponent:
          self._bad_value()
        match len(self._ieee754):
          case 2: break
          case 4:
            if value & ((1 << 13) - 1): break
            value >>= 13
            value &= 0x7fff
            if (sign):
              value |= 0x8000
            continue
          case 8:
            if value & ((1 << 29) - 1): break
            value >>= 29
            value &= 0x7fffffff
            if (sign):
              value |= 0x80000000
            continue
      self._value = value
      return
    
    def _bad_value(self):
      CBOR._error("Not a non-finite number: " + str(self._original))

    def is_simple(self):
      return self._value in [0x7e00 , 0x7c00 , 0xfc00]

    def set_sign(self, sign):
      mask = 1 << (len(self._ieee754) * 8 - 1)
      self._create_det_enc((self._value & (mask - 1)) | (mask if sign else 0))
      return self

    def is_nan(self):
      match len(self._ieee754):
        case 2: mask = 0x3ff
        case 4: mask = 0x7fffff
        case 8: mask = 0xfffffffffffff
      return (mask & self._value) != 0

    def get_sign(self):
      return self._ieee754[0] > 0x7f

    @classmethod
    def create_payload(cls, payload):
      CBOR._check_int_argument(payload)
      if (payload & 0x1fffffffffffff) != payload:
        CBOR._error("Payload out of range: " + payload)
      left64 = 0xfff0000000000000 if (payload & 0x10000000000000) else 0x7ff0000000000000
      return CBOR.NonFinite(left64 + CBOR._reverse_payload(payload & 0xfffffffffffff))

    def get_non_finite(self):
      """
      self.scan()
      """
      return self._value

    def _toNonFinite64(self, significand_length):
      nf64 = self._value
      nf64 &= (1 << significand_length) - 1
      nf64 = 0x7ff0000000000000 | (nf64 << (52 - significand_length))
      if self.get_sign():
        nf64 |= 0x8000000000000000
      return nf64 

    def get_payload(self):
      return CBOR._reverse_payload(self.get_non_finite64() & 0xfffffffffffff)

    def _internal_encode(self):
      return bytes([0xf9 + (len(self._ieee754) >> 2)]) + self._ieee754

    """
    def internalToString(cborPrinter): 
      if self.is_simple():
        cborPrinter.append(self.is_nan() ? "NaN" : self.get_sign() ? "-Infinity" : "Infinity")
      else:
        cborPrinter.append("float'").append(CBOR.toHex(self._ieee754)).append("'")
    """
  
    def _getLength(self):
      return len(self._ieee754)
  
    def _get(self):
      match len(self._ieee754):
        case 2: return self._toNonFinite64(10)
        case 4: return self._toNonFinite64(23)
      return self._value

    """
    def _getValue():
      return self._value
    """

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
      # Right, the decoder is yet to be written :)
      print(str(self._current))

  @classmethod
  def decode(cls, cbor_bytes):
    CBOR._check_bytes_argument(cbor_bytes)
    CBOR.init_decoder(io.BytesIO(cbor_bytes), len(cbor_bytes)).decode_with_options()

  @classmethod
  def init_decoder(cls, cbor_stream, max_length):
    return CBOR._Decoder(cbor_stream, max_length)
