################################################################
#                                                              #
#                 CBOR::Core API for Python3                   #
#                                                              #
# Author: Anders Rundgren (anders.rundgren.net@gmail.com)      #
# Repository: https://github.com/cyberphone/CBOR.py.           #
#                                                              #
# Note: this is a "Reference Implementation", not optimized    #
# for maximum performance.  It is assumed that a productified  #
# version of CBOR.py would be rewritten in C.                  #
################################################################

import struct
import math
import io
import base64
import datetime
import re

class CBOR:
        
    version = '1.0.0'

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
    
    _ESCAPE_CHARACTERS = [
    #   0    1    2    3    4    5    6    7
        1,   1,   1,   1,   1,   1,   1,   1, 
       98, 116, 110,   1, 102, 114,   1,   1,
        1,   1,   1,   1,   1,   1,   1,   1,
        1,   1,   1,   1,   1,   1,   1,   1,
        0,   0,  34,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,  92]

    def __init__(self):
        CBOR._error("Invalid operation")

    class _CborObject:
        def __init__(self):
            self._read_flag = False
            self._immutable_flag = False

        def __repr__(self):
            return self.to_string()

        def __str__(self):
            return self.to_string()
        
        def equals(self, object):
            if isinstance(object, CBOR._CborObject):
                if not CBOR._compare_byte_arrays(self.encode(),
                                                 object.encode()):
                    return True
            return False
        
        def clone(self):
            return CBOR.decode(self.encode())
        
        def __eq__(self, object):
            return self.equals(object)
        
        @property
        def length(self):
            if not hasattr(self, "_length"):
                CBOR._error("'CBOR." + type(self).__name__  +
                            "' does not support len()")
            return self._length()
        
        def __len__(self):
            return self.length
        
        def _immutable_test(self):
            if self._immutable_flag:
                CBOR._error('Map keys are immutable') 

        def _check_type_get_value(self, expected):
            if type(self).__name__ != expected:
                CBOR._error("Expected '" + 'CBOR.' + expected +
                            "', got 'CBOR." + type(self).__name__  + "'")
            self._read_flag = True
            return self._get()

        def get_bigint(self):
            return self._check_type_get_value('Int')
        
        def _get_checked_int(self, min, max):
            return CBOR._int_range_check(self.get_bigint(), min, max)

        def get_int8(self):
            return self._get_checked_int(-0x80, 
                                         0x7f)

        def get_uint8(self):
            return self._get_checked_int(0, 
                                         0xff)

        def get_int16(self):
            return self._get_checked_int(-0x8000, 
                                         0x7fff)

        def get_uint16(self):
            return self._get_checked_int(0, 
                                         0xffff)

        def get_int32(self):
            return self._get_checked_int(-0x80000000, 
                                         0x7fffffff)

        def get_uint32(self):
            return self._get_checked_int(0, 0xffffffff)

        def get_int53(self):
            return self._get_checked_int(-9007199254740991, 
                                         9007199254740991)

        def get_int64(self):
            return self._get_checked_int(-0x8000000000000000,
                                         0x7fffffffffffffff)

        def get_uint64(self):
            return self._get_checked_int(0, 
                                         0xffffffffffffffff)

        def get_int128(self):
            return self._get_checked_int(-0x80000000000000000000000000000000,
                                         0x7fffffffffffffffffffffffffffffff)

        def get_uint128(self):
            return self._get_checked_int(0, 
                                         0xffffffffffffffffffffffffffffffff)
        
        def _range_float(self, max):
            value = self.get_float64()
            if self.length > max:
                CBOR._range_error('float' + str(max * 8), str(value))
            return value

        def get_float16(self):
            return self._range_float(2)

        def get_float32(self):
            return self._range_float(4)

        def get_float64(self):
            return self._check_type_get_value('Float')

        def get_extended_float64(self):
            if isinstance(self, CBOR.NonFinite):
                match self.get_non_finite():
                    case 0x7e00: return math.nan
                    case 0x7c00: return math.inf
                    case 0xfc00: return -math.inf
                CBOR._error('get_extended_float64() only supports ' +
                            'simple" NaN (7e00)')
            return self.get_float64()
        
        def get_string(self):
            return self._check_type_get_value('String')

        def get_date_time(self):
            iso = self.get_string()
            # Fails on https://www.rfc-editor.org/rfc/rfc3339.html#section-5.8
            # Leap second 1990-12-31T15:59:60-08:00
            match = re.search(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})" +
                              r"(\.\d{1,9})?((\-|\+)\d{2}:\d{2}|Z)$", iso)
            if match:
                instant = datetime.datetime.fromisoformat(iso)
                CBOR._check_time_range(datetime.datetime.timestamp(instant))
                return instant
            CBOR._error("Invalid ISO format: \"{:s}\"".format(iso))

        def get_epoch_time(self):
            return datetime.datetime.fromtimestamp(CBOR._check_time_range(
                float(self.get_int53()) if isinstance(self, CBOR.Int) 
                                        else self.get_float64()),
                                                   datetime.UTC)
                
        def get_bytes(self):
            return self._check_type_get_value('Bytes')

        def get_boolean(self):
            return self._check_type_get_value('Boolean')

        def is_null(self):
            if type(self).__name__ == 'Null':
                self._read_flag = True
                return True
            return False
        
        def get_simple(self):
            return self._check_type_get_value('Simple')

        def get_non_finite64(self):
            return self._check_type_get_value('NonFinite')

        def encode(self):
            return self._internal_encode()
        
        def check_for_unread(self):
            self._traverse(None, True)

        def scan(self):
            self._traverse(None, False)
            return self

        def _traverse(self, holder_object, check):
            match type(self).__name__:
                case "Map":
                    for entry in self._entries:
                        self.get(entry._key)._traverse(entry._key, check)

                case "Array":
                    for object in self._objects:
                        object._traverse(self, check)
                
                case "Tag":
                    self.get()._traverse(self, check)

            if check:
                if not self._read_flag:
                    CBOR._error(("Data" if holder_object is None else 
                        "Array element" if isinstance(holder_object, 
                                                      CBOR.Array) else
                        "Tagged object " + 
                            str(holder_object.get_tag_number()) 
                        if isinstance(holder_object,CBOR.Tag) else 
                        "Map key " +
                            holder_object.to_diagnostic(False) + 
                            " with argument") +                    
                        " of type=CBOR." + type(self).__name__ + 
                        " with value=" + 
                            self.to_diagnostic(False) + " was never read")

            else:
                self._read_flag = True
  
        def get(self):
            CBOR._error('get() not available in: CBOR.' + type(self).__name__)

        def to_diagnostic(self, pretty_print):
            cbor_printer = CBOR._CborPrinter(
                CBOR._check_bool_argument(pretty_print))
            self._internal_to_string(cbor_printer)
            return cbor_printer.buffer

        def to_string(self):
            return self.to_diagnostic(True)


    #========================#  
    #  CBOR Wrapper Objects  #
    #========================#

    ##########################
    #       CBOR.Int         #
    ##########################
    class Int(_CborObject):
        def __init__(self, value):
            super().__init__()
            self._value = CBOR._check_int_argument(value)

        @staticmethod
        def create_int8(value):
            return CBOR._create_int(value, 
                                    -0x80, 
                                    0x7f)

        @staticmethod
        def create_uint8(value):
            return CBOR._create_int(value, 
                                    0, 
                                    0xff)

        @staticmethod
        def create_int16(value):
            return CBOR._create_int(value,
                                    -0x8000, 
                                    0x7fff)

        @staticmethod
        def create_uint16(value):
            return CBOR._create_int(value, 
                                    0, 
                                    0xffff)

        @staticmethod
        def create_int32(value):
            return CBOR._create_int(value,
                                    -0x80000000, 
                                    0x7fffffff)

        @staticmethod
        def create_uint32(value):
            return CBOR._create_int(value, 
                                    0, 
                                    0xffffffff)

        @staticmethod
        def create_int53(value):
            return CBOR._create_int(value, 
                                    -9007199254740991, 
                                    9007199254740991)

        @staticmethod
        def create_int64(value):
            return CBOR._create_int(value, 
                                    -0x8000000000000000,
                                    0x7fffffffffffffff)

        @staticmethod
        def create_uint64(value):
            return CBOR._create_int(value, 
                                    0,
                                    0xffffffffffffffff)
            
        @staticmethod
        def create_int128(value):
            return CBOR._create_int(value, 
                                    -0x80000000000000000000000000000000,
                                    0x7fffffffffffffffffffffffffffffff)

        @staticmethod
        def create_uint128(value):
            return CBOR._create_int(value,
                                    0, 
                                    0xffffffffffffffffffffffffffffffff)

        def _internal_encode(self):
            tag = CBOR._MT_UNSIGNED
            value = self._value
            if value < 0:
                tag = CBOR._MT_NEGATIVE
                value = ~value
            return CBOR._generic_header(tag, value)
        
        def _internal_to_string(self, cbor_printer):
            cbor_printer.append(str(self._value))
        
        def _get(self):
            return self._value
    
    ##########################
    #       CBOR.Float       #
    ##########################
    class Float(_CborObject):
        def __init__(self, value):
            super().__init__()
            self._value = CBOR._check_argument_type(value, 'float')
            """ 
            Catch the forbidden use-case.
            See: CBOR.Float.create_extended_float().
            """
            if not math.isfinite(value):
                CBOR._error("Not permitted: 'NaN/Infinity'")
            """ 
            Get the 8 bytes representing the IEEE-754 double. 
            """
            f64b = struct.pack('!d', value)
            """ 
            Deal with 0.0 and -0.0 separately.
            """
            if value == 0:
                self._encoded = f64b[0:2]
                return
            while True:
                f64bin = CBOR._bytes_to_uint(f64b)
                """
                Exponent bias difference: 1023 - 127
                """
                f32exp = ((f64bin & 0x7ff0000000000000) >> 52) - 0x380
                """
                Don't go into the non-finite space or underflow. 
                """
                if f32exp <= -23 or f32exp > 0xfe: break
                f32signif = f64bin & 0xfffffffffffff
                """ 
                The bits to be discarded must all be zero.
                Significand size difference: 52 - 23
                """
                if f32signif & 0x1fffffff: break
                """
                No bits dropped. Put significand in position.
                """
                f32signif >>= 29
                """ Finally, do we need to denormalize the number? """
                if f32exp <= 0:
                    """
                    Losing significand bits is not an option.
                    """
                    if f32signif & ((1 << (1 - f32exp)) - 1): break
                    """
                    No bits dropped. Denormalize. The implicit "1"
                    becomes explicit using subnormal representation.
                    """
                    f32signif += 0x800000
                    """
                    Put significand in position.
                    """
                    f32signif >>= (1 - f32exp)
                    """
                    Denormalized exponents are always zero.
                    """
                    f32exp = 0
                """
                Maybe we are done but we need to check
                if float16 is possible as well.
                """
                while True:
                    """
                    Exponent bias difference: 127 - 15
                    """
                    f16exp = f32exp - 0x70
                    """
                    Don't go into the non-finite space or underflow.
                    """
                    if f16exp <= -10 or f16exp > 0x1e: break
                    """
                    The bits to be discarded must all be zero.
                    Significand size difference: 23 - 10
                    """
                    if f32signif & 0x1fff: break
                    """
                    No bits dropped. Put significand in position.
                    """
                    f16signif = f32signif >> 13
                    if f16exp <= 0:
                        """
                        Losing significand bits is not an option.
                        """
                        if f16signif & ((1 << (1 - f16exp)) - 1): break
                        """
                        No bits dropped. Denormalize. The implicit "1"
                        becomes explicit using subnormal representation.
                        """
                        f16signif += 0x400
                        """
                        Put significand in position.
                        """
                        f16signif >>= (1 - f16exp)
                        """
                        Denormalized exponents are always zero.
                        """
                        f16exp = 0
                    """
                    Reached the end of the rope => float16.
                    """
                    self._encoded = CBOR._encode_16_bits(
                        ((f64b[0] & 0x80) << 8) + (f16exp << 10) + f16signif)
                    return
                """
                Exited inner loop  => float32.
                """
                f32bin = ((f64b[0] & 0x80) << 24) + (f32exp << 23) + f32signif
                self._encoded = (CBOR._encode_16_bits(f32bin >> 16) + 
                                 CBOR._encode_16_bits(f32bin & 0xffff))
                return
            """
            Exited outer loop => float64.
            """
            self._encoded = f64b

        @staticmethod
        def create_extended_float(value):
            if math.isfinite(CBOR._check_argument_type(value, 'float')):
                return CBOR.Float(value)
            """ 
            Not a "genuine" floating-point number.
            Handled as a separate data type.
            """
            nf = CBOR.NonFinite(CBOR._bytes_to_uint(struct.pack('!d', value)))
            if not nf.is_simple(): CBOR._error(
                "create_extended_float() does not support NaN with payloads")
            return nf

        @staticmethod
        def create_float32(value):
            return CBOR._return_converted(False, value)

        @staticmethod
        def create_float16(value):
            return CBOR._return_converted(True, value)

        def _internal_encode(self):
            return bytes([0xf9 + (len(self._encoded) >> 2)]) + self._encoded
        
        def _internal_to_string(self, cbor_printer):
            textual = str(self._value)
            e_pos = textual.find("e")
            if e_pos > 0 and textual.find(".") < 0:
                textual = textual[0:e_pos] + ".0" + textual[e_pos:]
            cbor_printer.append(textual)

        def _length(self):
            return len(self._encoded)
        
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
            return CBOR._encode_string(
                CBOR._MT_STRING, self._string.encode())
        
        def _internal_to_string(self, cbor_printer):
            cbor_printer.append('"')
            for q in range(len(self._string)):
                c = ord(self._string[q])
                if c <= 0x5c:
                    escaped_character = CBOR._ESCAPE_CHARACTERS[c]
                    if escaped_character:
                        cbor_printer.append('\\')
                        if escaped_character == 1:
                            cbor_printer.append("u00{:02x}".format(c))
                        else:
                            cbor_printer.append(chr(escaped_character))
                        continue;
                cbor_printer.append(chr(c))
            cbor_printer.append('"')
    
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
        
        def _internal_to_string(self, cbor_printer):
            cbor_printer.append("h'").append(self._string.hex()).append("'")
    
        def _get(self):
            return self._string

    ##########################
    #      CBOR.Boolean      #
    ##########################
    class Boolean(_CborObject):
        def __init__(self, value):
            super().__init__()
            self._value = CBOR._check_bool_argument(value)

        def _internal_encode(self):
            return bytes(
                [CBOR._SIMPLE_TRUE if self._value else CBOR._SIMPLE_FALSE])
        
        def _internal_to_string(self, cbor_printer):
            cbor_printer.append("true" if self._value else "false")
    
        def _get(self):
            return self._value
        
    ##########################
    #       CBOR.Null        #
    ##########################
    class Null(_CborObject):
        def __init__(self):
            super().__init__()

        def _internal_encode(self):
            return bytes([CBOR._SIMPLE_NULL])
        
        def _internal_to_string(self, cbor_printer):
            cbor_printer.append("null")

    ##########################
    #       CBOR.Array       #
    ##########################
    class Array(_CborObject):
        def __init__(self):
            super().__init__()
            self._objects = list()

        def add(self, object):
            self._immutable_test()
            self._objects.append(CBOR._cbor_argument_check(object))
            return self
        
        def get(self, index):
            self._read_flag = True
            return self._objects[self._index_check(
                index, len(self._objects) - 1)]
        
        def insert(self, index, object):
            self._immutable_test()
            self._objects.insert(
                self._index_check(index, len(self._objects)),
                CBOR._cbor_argument_check(object))
            return self

        def update(self, index, object):
            self._immutable_test()
            self._index_check(index, len(self._objects) - 1)
            previous = self._objects[index]
            self._objects[index] = CBOR._cbor_argument_check(object)
            return previous

        def remove(self, index):
            self._immutable_test()
            return self._objects.pop(
                self._index_check(index, len(self._objects) - 1))

        def to_array(self):
            array = list()
            for object in self._objects:
                array.append(object)
            return array

        def _index_check(self, index, max):
            if CBOR._check_int_argument(index) > max or index < 0:
                CBOR._error("Index out of range: " + str(index))
            return index
        
        def _encode_body(self, header):
            for object in self._objects:
                header += object._internal_encode()
            return header

        def encode_as_sequence(self):
            return self._encode_body(bytearray())
                
        def _internal_encode(self):
            return self._encode_body(
                CBOR._generic_header(CBOR._MT_ARRAY, len(self._objects)))
        
        def _internal_to_string(self, cbor_printer):
            if cbor_printer.arrayFolding(self):
                cbor_printer.beginList('[')
                not_first = False
                for object in self._objects:
                    if not_first:
                        cbor_printer.append(',')
                    not_first = True
                    cbor_printer.newlineAndIndent()
                    object._internal_to_string(cbor_printer)
                cbor_printer.endList(not_first, ']')
            else:
                cbor_printer.append('[')
                not_first = False
                for object in self._objects:
                    if not_first:
                        cbor_printer.append(',').space()
                    not_first = True
                    object._internal_to_string(cbor_printer)
                cbor_printer.append(']')
        
        def _length(self):
            return len(self._objects)
 
    ##########################
    #        CBOR.Map        #
    ##########################
    class Map(_CborObject):
        def __init__(self):
            super().__init__()
            self._entries = list()
            self._pre_sorted_keys = False
            self._last_lookup = 0

        def set(self, key, object):
            self._immutable_test()
            new_entry = CBOR._Entry(key, object)
            self._make_immutable(key)
            insert_index = len(self._entries)
            if insert_index:
                end_index = insert_index - 1
                if self._pre_sorted_keys:
                    """ Normal case for deterministic decoding. """
                    if self._entries[end_index]._compare_and_test(new_entry):
                        CBOR._error("Non-deterministic order for key: " + str(key))
                else:
                    """
                    Programmatically created key or the result of
                    unconstrained decoding.  Then we need to test and
                    sort (always produce deterministic CBOR).
                    The algorithm is based on binary sort and insertion.
                    """
                    insert_index = 0
                    start_index = 0
                    while start_index <= end_index:
                        mid_index = (end_index + start_index) >> 1
                        if new_entry._compare_and_test(
                            self._entries[mid_index]):
                            """
                            New key is bigger than the looked up entry.
                            Preliminary assumption: this is the one,
                            but continue.
                            """
                            insert_index = start_index = mid_index + 1
                        else:
                            """ 
                            New key is smaller, search lower parts
                            of the array.
                            """
                            end_index = mid_index - 1
            """
            If insertIndex == len(self._entries), the key will be appended.
            If insertIndex == 0, the key will be first in the list.
            """
            self._entries.insert(insert_index, new_entry)
            return self

        """
        setDynamic(dynamic):
        return dynamic(this);
        """

        def _lookup(self, key, mustExist):
            encoded_key = CBOR._cbor_argument_check(key).encode()
            start_index = 0
            end_index = len(self._entries) - 1
            while start_index <= end_index:
                mid_index = (end_index + start_index) >> 1
                entry = self._entries[mid_index]
                diff = entry._compare(encoded_key)
                if diff == 0:
                    self._last_lookup = mid_index
                    return entry
                if diff < 0:
                    start_index = mid_index + 1
                else:
                    end_index = mid_index - 1
            if mustExist:
                CBOR._error("Missing key: " + str(key))
            return None

        def update(self, key, object, existing=True):
            self._immutable_test()
            entry = self._lookup(key, existing)
            if entry:
                previous = entry._object
                entry._object = CBOR._cbor_argument_check(object)
            else:
                previous = None
                self.set(key, object)
            return previous

        def merge(self, map):
            self._immutable_test()
            if not isinstance(map, CBOR.Map):
                CBOR._error("Argument must be of type CBOR.Map")
            for entry in map._entries:
                self.set(entry._key, entry._object)
            return self

        def get(self, key):
            self._read_flag = True
            return self._lookup(key, True)._object
   
        def get_conditionally(self, key, default_object=None):
            entry = self._lookup(key, False)
            # Note: if default_object calls __len__
            if default_object is not None: CBOR._cbor_argument_check(default_object)
            return entry._object if entry else default_object

        def get_keys(self):
            keys = list()
            for entry in self._entries:
                keys.append(entry._key)
            return keys

        def remove(self, key):
            self._immutable_test()
            target_entry = self._lookup(key, True)
            self._entries.pop(self._last_lookup)
            return target_entry._object

        def contains_key(self, key):
            return self._lookup(key, False) != None

        def _internal_encode(self):
            encoded = CBOR._generic_header(CBOR._MT_MAP, len(self._entries))
            for entry in self._entries:
                encoded += entry._encoded_key + entry._object.encode()
            return encoded

        def _internal_to_string(self, cbor_printer):
            not_first = False
            cbor_printer.beginList("{")
            for entry in self._entries:
                if not_first:
                    cbor_printer.append(",")
                not_first = True
                cbor_printer.newlineAndIndent()
                entry._key._internal_to_string(cbor_printer)
                cbor_printer.append(":").space()
                entry._object._internal_to_string(cbor_printer)
            cbor_printer.endList(not_first, "}")

        def set_sorting_mode(self, pre_sorted_keys):
            self._pre_sorted_keys = pre_sorted_keys
            return self

        def _make_immutable(self, object):
            object._immutable_flag = True
            if isinstance(object, CBOR.Map):
                for entry in object._entries:
                    self._make_immutable(entry._object)
            elif isinstance(object, CBOR.Array):
                for value in object._objects:
                    self._make_immutable(value)

        def _length(self):
            return len(self._entries)

    """ Support class to CBOR.Map. """    
    class _Entry:
        def __init__(self, key, object):
            self._key = CBOR._cbor_argument_check(key)
            self._encoded_key = key.encode() # Yes, keys are immutable.
            self._object = CBOR._cbor_argument_check(object)

        def _compare(self, encoded_key):
            return CBOR._compare_byte_arrays(self._encoded_key, encoded_key)

        def _compare_and_test(self, entry):
            diff = self._compare(entry._encoded_key)
            if diff == 0:
                CBOR._error("Duplicate key: " + str(self._key))
            return diff > 0

    ##########################
    #       CBOR.Tag         #
    ##########################
    class Tag(_CborObject):

        TAG_DATE_TIME  = 0
        TAG_EPOCH_TIME = 1
        TAG_COTX       = 1010

        __TAG_BIG_POS  = 2
        __TAG_BIG_NEG  = 3

        __ERR_COTX     = "Invalid COTX object: "
        __ERR_DATE     = "Invalid ISO date/time object: "
        __ERR_EPOCH    = "Invalid Epoch time object: "

        def __init__(self, tag_number, object):
            super().__init__()
            self._cotx_object = None
            self._date_time = None
            self._epoch_time = None
            self._tag_number = CBOR._check_int_argument(tag_number)
            self._object = CBOR._cbor_argument_check(object)
            if self._tag_number < 0 or self._tag_number >= 0x10000000000000000:
                CBOR._error("Tag number is out of range")
            match (self._tag_number):
                case CBOR.Tag.__TAG_BIG_POS | CBOR.Tag.__TAG_BIG_NEG:
                    CBOR._error("Tag number reserved for 'bigint'")
                case CBOR.Tag.TAG_DATE_TIME:
                    # Note: clone() because we have mot read it really.
                    self._date_time = object.clone().get_date_time()
                case CBOR.Tag.TAG_EPOCH_TIME:
                    # Note: clone() because we have mot read it really.
                    self._epoch_time = object.clone().get_epoch_time()
                case CBOR.Tag.TAG_COTX:
                    if not isinstance(object, CBOR.Array) or object.length != 2:
                        self._error_in_object(CBOR.Tag.__ERR_COTX)
                    self._cotx_id = object.get(0).get_string()
                    self._cotx_object = object.get(1)

        def get_date_time(self):
            if self._date_time is None:
                self._error_in_object(CBOR.Tag.__ERR_DATE)
            self._object.scan()
            return self._date_time

        def get_epoch_time(self):
            if self._epoch_time is None:
                self._error_in_object(CBOR.Tag.__ERR_EPOCH)
            self._object.scan()
            return self._epoch_time

        def _error_in_object(self, message):
            CBOR._error(message + self.to_diagnostic(False))

        def _internal_encode(self):
            return (CBOR._generic_header(CBOR._MT_TAG, self._tag_number) +
                    self._object.encode())

        def _internal_to_string(self, cbor_printer):
            cbor_printer.append(str(self._tag_number)).append('(')
            if self._cotx_object is None:
                self._object._internal_to_string(cbor_printer)
            else:
                cbor_printer.append('[')
                self._object.get(0)._internal_to_string(cbor_printer)
                cbor_printer.append(',').space()
                self._object.get(1)._internal_to_string(cbor_printer)
                cbor_printer.append(']')
            cbor_printer.append(')')

        def get_tag_number(self):
            return self._tag_number
    
        def get(self):
            self._read_flag = True
            return self._object

        def _check_cotx(self):
            if self._cotx_object is None:
                self._error_in_object(CBOR.Tag.__ERR_COTX)

        @property
        def cotx_id(self):
            self._check_cotx()
            return self._cotx_id

        @property
        def cotx_object(self):
            self._check_cotx()
            return self._cotx_object

    ##########################
    #      CBOR.Simple       #
    ##########################
    class Simple(_CborObject):
        def __init__(self, value):
            super().__init__()
            self._value = CBOR._check_int_argument(value)
            if value < 0 or value > 255 or (value > 23 and value < 32):
                CBOR._error("Simple value out of range: " + str(value))

        def _internal_encode(self):
            return CBOR._generic_header(CBOR._MT_SIMPLE, self._value)

        def _internal_to_string(self, cbor_printer):
            cbor_printer.append("simple(" + str(self._value) + ")")

        def _get(self):
            return self._value

    ##########################
    #     CBOR.NonFinite     #
    ##########################
    class NonFinite(_CborObject):
        def __init__(self, value):
            super().__init__()
            self._original = CBOR._check_int_argument(value)
            if value < 0: self._bad_value()
            self._create_det_enc(value)

        def _create_det_enc(self, value):
            while True:
                """ Create a byte representation of the value. """
                self._ieee754 = bytearray()
                i = value
                while True:
                    self._ieee754 += bytes([i & 0xff])
                    i >>= 8
                    if i == 0: break
                self._ieee754.reverse()
                """
                Check that the syntax matches a non-finite number.
                """
                match len(self._ieee754):
                    case 2: exponent = 0x7c00
                    case 4: exponent = 0x7f800000
                    case 8: exponent = 0x7ff0000000000000
                    case _: self._bad_value()
                if (value & exponent) != exponent: self._bad_value()
                """
                All is good, now apply "preferred serialization".
                """
                sign = self._ieee754[0] > 0x7f
                match len(self._ieee754):
                    case 2: break
                    case 4:
                        if value & ((1 << 13) - 1): break
                        value >>= 13
                        value &= 0x7fff
                        if sign: value |= 0x8000
                    case 8:
                        if value & ((1 << 29) - 1): break
                        value >>= 29
                        value &= 0x7fffffff
                        if sign: value |= 0x80000000
            """ 
            Exited loop => the perfect ("preferred")
            serialization has been found.
            """
            self._value = value
        
        def _bad_value(self):
            CBOR._error("Not a non-finite number: " + str(self._original))

        def is_simple(self):
            return self._value in [0x7e00 , 0x7c00 , 0xfc00]

        def set_sign(self, sign):
            mask = 1 << (len(self._ieee754) * 8 - 1)
            self._create_det_enc(
                (self._value & (mask - 1)) | (mask if sign else 0))
            return self

        def is_nan(self):
            match len(self._ieee754):
                case 2: mask = 0x3ff
                case 4: mask = 0x7fffff
                case 8: mask = 0xfffffffffffff
            return (mask & self._value) != 0

        def get_sign(self):
            return self._ieee754[0] > 0x7f

        @staticmethod
        def create_payload(payload):
            CBOR._check_int_argument(payload)
            if (payload & 0x1fffffffffffff) != payload:
                CBOR._error("Payload out of range: " + str(payload))
            left64 = (0xfff0000000000000 if (payload & 0x10000000000000)
                                         else 0x7ff0000000000000)
            return CBOR.NonFinite(left64 + 
                CBOR._reverse_payload(payload & 0xfffffffffffff))

        def get_non_finite(self):
            self.scan()
            return self._value

        def _to_non_finite64(self, significand_length):
            nf64 = self._value
            nf64 &= (1 << significand_length) - 1
            nf64 = 0x7ff0000000000000 | (nf64 << (52 - significand_length))
            if self.get_sign():
                nf64 |= 0x8000000000000000
            return nf64 

        def get_payload(self):
            return (0x10000000000000 if self.get_sign()
                                     else 0) + CBOR._reverse_payload(
                self.get_non_finite64() & 0xfffffffffffff)

        def _internal_encode(self):
            return bytes([0xf9 + (len(self._ieee754) >> 2)]) + self._ieee754

        def _internal_to_string(self, cbor_printer): 
            if self.is_simple():
                cbor_printer.append("NaN" if self.is_nan()
                    else "-Infinity" if self.get_sign() else "Infinity")
            else: 
                cbor_printer.append("float'").append(
                    self._ieee754.hex()).append("'")
    
        def _length(self):
            return len(self._ieee754)
    
        def _get(self):
            match len(self._ieee754):
                case 2: return self._to_non_finite64(10)
                case 4: return self._to_non_finite64(23)
            return self._value

    #======================#  
    #     CBOR Decoder     #
    #======================#

    SEQUENCE_MODE           = 0x1
    LENIENT_MAP_DECODING    = 0x2
    LENIENT_NUMBER_DECODING = 0x4

    class _Decoder:
        def __init__(self, cbor_stream, options, max_length):
            CBOR._check_int_argument(max_length)
            CBOR._check_int_argument(options)
            if not isinstance(cbor_stream, io.BufferedIOBase):
                CBOR._error("Unexpected stream type: " + 
                            type(cbor_stream).__name__)
            self._cbor_stream = cbor_stream
            self._sequence_mode = options & CBOR.SEQUENCE_MODE
            self._strict_maps = not (options & CBOR.LENIENT_MAP_DECODING)
            self._strict_numbers = not (options & CBOR.LENIENT_NUMBER_DECODING)
            self._max_length = max_length
            self._max_nesting_level = 100

            self._byte_count = 0
            self._nesting_level = 0
    
        def decode_with_options(self):
            self._at_first_byte = True
            cbor_object = self._get_object()
            if self._sequence_mode:
                if self._at_first_byte:
                    return None
            elif self._cbor_stream.read(1):
                CBOR._error("Unexpected data found after CBOR object")
            return cbor_object
        
        def _out_of_limit_test(self, length):
            self._byte_count += length
            if self._byte_count > self._max_length:
                CBOR._error("Exceeded set limit: max_length={:n}".format(
                    self._max_length))
    
        def _eof_error(self):
            CBOR._error("Malformed CBOR, trying to read past EOF")

        def enter_level(self):
            self._nesting_level += 1
            if self._nesting_level > self._max_nesting_level:
                CBOR._error("Structure nesting level exceeding: " + 
                            self._max_nesting_level)

        def set_max_nesting_level(self, max_level):
            self._max_nesting_level = CBOR._check_int_argument(max_level)
            return self

        def _read_byte(self):
            one_byte = self._cbor_stream.read(1)
            if one_byte is None or len(one_byte) == 0:
                if self._sequence_mode and self._at_first_byte:
                    return 0
                self._eof_error()
            self._at_first_byte = False
            self._out_of_limit_test(1)
            return one_byte[0]

        def _read_bytes(self, length):
            if not length:
                return bytes() # Python fix
            self._out_of_limit_test(length)
            byte_string = self._cbor_stream.read(length)
            if byte_string is None or len(byte_string) < length: # Python fix
                self._eof_error()
            return byte_string

        def _unsupported_tag(self, tag):
            CBOR._error("Unsupported tag: 0x{:02x}".format(tag))

        def _print_float_det_err(self, decoded):
            CBOR._error(
                "Non-deterministically encoded \"float\": " +
                "{:2x}{:s}".format(
                    CBOR._SIMPLE_FLOAT16 + (len(decoded) >> 2),
                    decoded.hex()))

        def _decode_float(self, length, mask, prefix):
            decoded = self._read_bytes(length)
            value = CBOR._bytes_to_uint(decoded)
            """
            Is it a non-finite number?
            """
            if (value & mask) == mask:
                """
                Yes, deal with it as a distinct data type.
                """
                non_finite = CBOR.NonFinite(value)
                if self._strict_numbers and non_finite._value != value:
                    self._print_float_det_err(decoded)
                return non_finite
            """
            No, it is a "regular" number.
            """
            cbor_float = CBOR.Float(struct.unpack(prefix, decoded)[0])
            if self._strict_numbers and cbor_float._encoded != decoded:
                self._print_float_det_err(decoded)
            return cbor_float

        def _get_object(self):
            tag = self._read_byte()
            """ 
            Begin with CBOR types that are uniquely defined by the tag byte.
            """
            match tag:
                case CBOR._TAG_BIG_NEGATIVE | CBOR._TAG_BIG_UNSIGNED:
                    position = self._byte_count
                    byte_array = self._get_object().get_bytes()
                    if (self._strict_numbers and 
                        (len(byte_array) <= 8 or not byte_array[0])):
                        CBOR._error(
                            "Non-deterministically encoded \"bigint\" ()" +
                            "tag={:02x}, argument={:s})".format(
                                tag, byte_array.hex()))
                    value = CBOR._bytes_to_uint(byte_array)
                    return CBOR.Int(value if tag == CBOR._TAG_BIG_UNSIGNED
                                          else ~value)

                case CBOR._SIMPLE_FLOAT16:
                    return self._decode_float(2, 0x7c00, "!e")

                case CBOR._SIMPLE_FLOAT32:
                    return self._decode_float(4, 0x7f800000, "!f")

                case CBOR._SIMPLE_FLOAT64:
                    return self._decode_float(8, 0x7ff0000000000000, "!d")

                case CBOR._SIMPLE_NULL:
                    return CBOR.Null()

                case CBOR._SIMPLE_TRUE | CBOR._SIMPLE_FALSE:
                    return CBOR.Boolean(tag == CBOR._SIMPLE_TRUE)
            """ 
            Then decode CBOR types that blend length of data in the tag byte.
            """
            n = tag & 0x1f
            if n > 27:
                self._unsupported_tag(tag)
            if n > 23:
                """ 
                For 1, 2, 4, and 8 byte N.
                """
                q = 1 << (n - 24)
                mask = 0xffffffff << ((q >> 1) * 8)
                n = 0
                while True:
                    q -= 1
                    if q < 0: break
                    n <<= 8
                    n += self._read_byte()
                """
                If the upper half (for 2, 4, 8 byte N) of N or a single byte
                N is zero, a shorter variant should have been used.
                In addition, N must be > 23. 
                """
                if self._strict_numbers and (n < 24 or not (mask & n)):
                    CBOR._error("Non-deterministically encoded primitive. " +
                                "Initial byte: 0x{:02x}".format(tag))
            """
            N successfully decoded, now switch on major type
            (upper three bits).
            """
            match tag & 0xe0:
                case CBOR._MT_SIMPLE:
                    return CBOR.Simple(n)

                case CBOR._MT_TAG:
                    self.enter_level()
                    cborTag = CBOR.Tag(n, self._get_object())
                    self._nesting_level -= 1
                    return cborTag

                case CBOR._MT_UNSIGNED:
                    return CBOR.Int(n)

                case CBOR._MT_NEGATIVE:
                    return CBOR.Int(~n)

                case CBOR._MT_BYTES:
                    return CBOR.Bytes(self._read_bytes(n))

                case CBOR._MT_STRING:
                    return CBOR.String(self._read_bytes(n).decode())

                case CBOR._MT_ARRAY:
                    self.enter_level()
                    cborArray = CBOR.Array()
                    for q in range(n):
                        cborArray.add(self._get_object())
                    self._nesting_level -= 1
                    return cborArray

                case CBOR._MT_MAP:
                    self.enter_level()
                    cborMap = CBOR.Map().set_sorting_mode(self._strict_maps)
                    for q in range(n):
                        cborMap.set(self._get_object(), self._get_object())
                    self._nesting_level -= 1
                    """ 
                    Programmatically added elements sort automatically. 
                    """
                    return cborMap.set_sorting_mode(False)

                case _:
                    self._unsupported_tag(tag)

        def decodeWithOptions(self):
            self._at_first_byte = True
            object = self._get_object()
            if self._sequence_mode:
                if self._at_first_byte:
                    return None
            elif self._byte_count < self.maxLength:
                CBOR._error("Unexpected data encountered after CBOR object")
            return object

        def get_byte_count(self):
            return self._byte_count

    
    #==============================#
    #  Diagnostic Notation Parser  #
    #==============================#

    class _DiagnosticNotation:
        def __init__(self, cbor_text, sequence_mode):
            self.cbor_text = CBOR._check_argument_type(cbor_text, 'str')
            self.sequence_mode = sequence_mode
            self.index = 0

        class ParserError(Exception):
            def __init__(self, msg):
                super().__init__(msg)
 #               self.__suppress_context__ = True
 #               sys.tracebacklimit = 0
    
        def build_error(self, error):
            pass
            """ Unsurprisingly, error handling turned out 
            to be the most complex part...
            """
            start = self.index - 100
            if start < 0:
                start = 0
            line_pos = 0
            while start < self.index - 1:
                temp = start
                start += 1
                if self.cbor_text[temp] == '\n':
                    line_pos = start
            complete = ''
            if self.index > 0 and self.cbor_text[self.index - 1] == '\n':
                self.index -= 1
            end_line = self.index
            while end_line < len(self.cbor_text):
                if self.cbor_text[end_line] == '\n':
                    break
                end_line += 1
            q = line_pos
            while q < end_line:
                complete += self.cbor_text[q]
                q += 1
            complete += '\n'
            q = line_pos
            while q < self.index:
                complete += '-'
                q += 1
            line_number = 1
            q = 0
            while q < self.index - 1:
                if self.cbor_text[q] == '\n':
                    line_number += 1
                q += 1
            return ("\n" + complete + "^\n\nError in line " +
                    str(line_number) + ". " + error)
        
        def parser_error(self, error):
            raise CBOR._DiagnosticNotation.ParserError(error)

        def read_sequence_to_eof(self):
            try:
                sequence = list()
                self.scan_non_signficant_data()
                while self.index < len(self.cbor_text):
                    if len(sequence):
                        if self.sequence_mode:
                            self.scan_for(",")
                        else:
                            self.read_char()
                            self.parser_error("Unexpected data after token")
                    sequence.append(self.get_object())
                if not len(sequence) and not self.sequence_mode:
                    self.read_char()
                return sequence
            except Exception as e:
                message = repr(e)
                i = message.find("Error('")
                if i >= 0:
                    message = message[i + 7:len(message) - 2]
                raise CBOR.Exception(self.build_error(message)) from None

        def get_object(self):
            self.scan_non_signficant_data()
            cbor_bbject = self.get_raw_object()
            self.scan_non_signficant_data()
            return cbor_bbject
    
        def continue_list(self, valid_stop):
            if self.next_char() == ',':
                self.read_char()
                return True
            actual = self.read_char()
            if actual != valid_stop:
                self.parser_error(
                    "Expected: ',' or '" + valid_stop + 
                    "' actual: " + self.to_readable_char(actual))
            self.index -= 1
            return False
    
        def get_raw_object(self):
            match self.read_char():

                case '<':
                    self.scan_for("<")
                    sequence = bytearray()
                    self.scan_non_signficant_data()
                    while (self.read_char() != '>'):
                        self.index -= 1
                        while True:
                            sequence += self.get_object().encode()
                            if not self.continue_list('>'): break
                    self.scan_for(">")
                    return CBOR.Bytes(sequence)
            
                case '[':
                    array = CBOR.Array()
                    self.scan_non_signficant_data()
                    while self.read_char() != ']':
                        self.index -= 1
                        while True:
                            array.add(self.get_object())
                            if not self.continue_list(']'): break
                    return array
            
                case '{':
                    map = CBOR.Map()
                    self.scan_non_signficant_data()
                    while self.read_char() != '}':
                        self.index -= 1
                        while True:
                            key = self.get_object()
                            self.scan_for(":")
                            map.set(key, self.get_object())
                            if not self.continue_list('}'): break
                    return map
                
                case '\'':
                    return self.get_string(True)
                    
                case '"':
                    return self.get_string(False)

                case 'h':
                    return self.get_bytes(False)

                case 'b':
                    if self.next_char() == '3':
                        self.scan_for("32'")
                        self.parser_error("b32 not implemented")
                    self.scan_for("64")
                    return self.get_bytes(True)
                    
                case 't':
                    self.scan_for("rue")
                    return CBOR.Boolean(True)
                
                case 'f':
                    if self.next_char() == 'a':
                        self.scan_for("alse")
                        return CBOR.Boolean(False)
                    self.scan_for('loat')
                    float_bytes = self.get_bytes(False).get_bytes()
                    if len(float_bytes) not in [2, 4, 8]:
                        self.parser_error(
                            "Argument must be a 16, 32, or 64-bit " +
                            "floating-point number")
                    return CBOR.init_decoder(
                        io.BytesIO(bytes(
                            [0xf9 + (len(float_bytes) >> 2)]) + float_bytes),
                        CBOR.LENIENT_NUMBER_DECODING,
                        100).decode_with_options()
                
                case 'n':
                    self.scan_for("ull")
                    return CBOR.Null()

                case 's':
                    self.scan_for("imple(")
                    return self.simple_type()

                case '-':
                    if self.read_char() == 'I':
                        self.scan_for("nfinity")
                        return CBOR.NonFinite(0xfc00)
                
                    return self.get_number_or_tag(True)

                case '0' | '1' | '2' | '3' | '4' |\
                    '5' | '6' | '7' | '8' | '9':
                    return self.get_number_or_tag(False)

                case 'N':
                    self.scan_for("aN")
                    return CBOR.NonFinite(0x7e00)

                case 'I':
                    self.scan_for("nfinity")
                    return CBOR.NonFinite(0x7c00)
                    
                case _:
                    self.index -= 1
                    self.parser_error(
                        "Unexpected character: " + 
                        self.to_readable_char(self.read_char()))

        def simple_type(self):
            token = ''
            while True:
                match self.next_char():
                    case ')':
                        break

                    case '+' | '-' | 'e' | '.':
                        self.parser_error("Syntax error")

                    case _:
                        token += self.read_char()
                        continue

            self.read_char()
            # clone() converts a numerical Simple into Boolean etc. if applicable. 
            return CBOR.Simple(int(token.strip())).clone()

        def get_number_or_tag(self, negative):
            token = ''
            self.index -= 1
            prefix = None
            if self.read_char() == '0' and self.next_char() in ['b' , 'o' , 'x']:
                prefix = '0' + self.read_char()
            if prefix is None:
                self.index -= 1
            floating_point = False
            while True:
                token += self.read_char()
                match self.next_char():
                    case '\u0000' | ' ' | '\n' | '\r' | '\t' | ',' |\
                         ':' | '>' | ']' | '}' | '/' | '#' | '(' | ')':
                        break

                    case '.' | 'e':
                        if prefix is None:
                            floating_point = True
                    
                    case '_':
                        if prefix is None:
                            self.parser_error("'_' is only permitted for " +
                                              "0b, 0o, and 0x numbers")
                        self.read_char()

            if floating_point:
                self.test_for_non_decimal(prefix)
                value = float(token)
                # Implicit overflow is not permitted
                if not math.isfinite(value):
                    self.parser_error("Floating point value out of range")
                return CBOR.Float(-value if negative else value)
            if self.next_char() == '(':
                # Do not accept '-', 0xhhh, or leading zeros
                self.test_for_non_decimal(prefix)
                if negative or (len(token) > 1 and token[0] == '0'):
                    self.parser_error("Tag syntax error")
                self.read_char()
                tag_number = int(token)
                cbor_tag = CBOR.Tag(tag_number, self.get_object())
                self.scan_for(")")
                return cbor_tag
            base = 10
            match prefix:
                case "0x": base = 16
                case "0o": base = 8
                case "0b": base = 2
            integer = int(token, base)
            return CBOR.Int(-integer if negative else integer)

        def test_for_non_decimal(self, non_decimal):
            if non_decimal:
                self.parser_error("0b, 0o, and 0x prefixes " +
                                  "are only permited for integers")

        def next_char(self):
            if self.index == len(self.cbor_text): return chr(0)
            c = self.read_char()
            self.index -= 1
            return c

        def to_readable_char(self, c):
            char_code = ord(c[0]);
            return ("\\u00{:2x}".format(char_code) 
                    if char_code < 0x20 else ("'" + c + "'"))

        def scan_for(self, expected):
            for i in range(len(expected)):
                c = expected[i]
                actual = self.read_char()
                if c != actual:
                    self.parser_error("Expected: '" + c + "' actual: " + 
                                      self.to_readable_char(actual))

        def get_string(self, byteString):
            s = ''
            while True:
                c = self.read_char()
                match c:
                    # Control character handling
                    case '\r':
                        if self.next_char() == '\n':
                            continue
                        c = '\n'

                    case '\n':
                        pass

                    case '\\':
                        c = self.read_char()
                        match c:
                            case '\n':
                                continue

                            case '\'' | '"' | '\\':
                                pass

                            case 'b':
                                c = '\b'

                            case 'f':
                                c = '\f'

                            case 'n':
                                c = '\n'

                            case 'r':
                                c = '\r'

                            case 't':
                                c = '\t'

                            case 'u':
                                u16 = 0
                                for i in range(4):
                                    u16 = (u16 << 4) + int(self.read_char(), 16)
                                if u16 >= 0xd800 and u16 < 0xdc00:
                                    # Surrogate pair assumed
                                    self.scan_for("\\u")
                                    low = 0
                                    for i in range(4):
                                        low = ((low << 4) + 
                                                int(self.read_char(), 16))
                                    if low < 0xdc00:
                                        self.parser_error(
                "Invalid UTF-16 surrogate pair: {:4X} {:4X}".format(u16, low))
                                    c = (CBOR._encode_16_bits(u16) + 
                                         CBOR._encode_16_bits(low)).decode(
                                             "utf-16-be")
                                else:
                                    c = chr(u16)
                    
                            case _:
                                self.parser_error(
                                    "Invalid escape character " + 
                                    self.to_readable_char(c))
                    
                    case '"':
                        if not byteString:
                            return CBOR.String(s)
                        

                    case '\'':
                        if byteString:
                            return CBOR.Bytes(s.encode())
                    
                    case _:
                        if ord(c[0]) < 0x20:
                            self.parser_error(
                                "Unexpected control character: " + 
                                self.to_readable_char(c))

                s += c
    
        def get_bytes(self, b64):
            token = ''
            self.scan_for("'")
            while True:
                c = self.read_char()
                match c:
                    case '\'':
                        if b64 and token.find("=") < 0:
                            for i in range(-len(token) % 4): # Python fix
                                token += '='
                        return CBOR.Bytes(
                            base64.urlsafe_b64decode(token) if
                                b64 else bytes.fromhex(token))

                    case ' ' | '\r' | '\n' | '\t':
                        continue

                    case _:
                        token += c
                        continue

        def read_char(self):
            if self.index >= len(self.cbor_text):
                self.parser_error("Unexpected EOF")
            temp = self.index
            self.index += 1
            return self.cbor_text[temp]

        def scan_non_signficant_data(self):
            while self.index < len(self.cbor_text):
                match self.next_char():
                    case ' ' | '\n' | '\r' | '\t':
                        self.read_char()
                        continue

                    case '/':
                        self.read_char()
                        while (self.read_char() != '/'):
                            """ No-Op """
                        continue

                    case '#':
                        self.read_char()
                        while (self.index < len(self.cbor_text) and
                                    self.read_char() != '\n'):
                            """ No-Op """
                        continue

                    case _:
                        return
    

    #================================#
    #      CBOR. Public Methods      #
    #================================#

   ###################################
    #          CBOR.decode()         #
    #       CBOR.init_decoder()      #
    ##################################

    @staticmethod
    def decode(cbor_bytes):
        CBOR._check_bytes_argument(cbor_bytes)
        return CBOR.init_decoder(io.BytesIO(cbor_bytes), 
                                 0, len(cbor_bytes)).decode_with_options()

    @staticmethod
    def init_decoder(cbor_stream, options, max_length):
        return CBOR._Decoder(cbor_stream, options, max_length)

    ###################################
    #      CBOR.from_diagnostic()     #
    #    CBOR.from_diagnostic_seq()   #
    ###################################

    @staticmethod
    def from_diagnostic(cborText):
        return CBOR._DiagnosticNotation(cborText, 
                                        False).read_sequence_to_eof()[0]

    @staticmethod
    def from_diagnostic_seq(cborText):
        return CBOR._DiagnosticNotation(cborText, 
                                        True).read_sequence_to_eof()

    ####################################
    #     CBOR.create_epoch_time()     #
    #     CBOR.create_date_time()      #
    ####################################

    @staticmethod
    def create_epoch_time(instant, millis):
        epoch = CBOR._check_time_parameters(instant, millis, True)
        return (CBOR.Float(epoch) if isinstance(epoch, float) 
                                  else CBOR.Int(epoch))
    
    def create_date_time(instant, millis, utc):
        epoc = CBOR._check_time_parameters(instant, millis, utc)
        iso_string = datetime.datetime.fromtimestamp(
            epoc, datetime.UTC).isoformat()
        i = iso_string.find("+00:00")
        if i > 0:
            iso_string = CBOR._remove_trailing_zeros(iso_string[0:i]) + "Z"
        if not utc:
            """
            This is very strange but there is no local timezone to find.
            """
            temp = local = CBOR._remove_trailing_zeros(
                datetime.datetime.fromtimestamp(epoc).isoformat())
            true_iso = datetime.datetime.timestamp(
                datetime.datetime.fromisoformat(iso_string))
            local_iso = datetime.datetime.timestamp(
                datetime.datetime.fromisoformat(temp + "Z"))
            diff = int(local_iso - true_iso)
            iso_string = "{:s}+{:02n}:{:02n}".format(
                local, diff / 3600, diff % 3600)
        return CBOR.String(iso_string)
    
        
    #================================#
    #    Internal Support Methods    #
    #================================#

    class _CborPrinter:

        def __init__(self, pretty_print):
            self.pretty_print = pretty_print
            self.indentation_level = 0
            self.start_of_line = 0
            self.buffer = ''

        def beginList(self, endChar):
            self.indentation_level += 1
            self.buffer += endChar

        def append(self, string):
            self.buffer += string
            return self

        def space(self):
            if self.pretty_print:
                self.buffer += ' '

        def arrayFolding(self, array):
            if self.pretty_print:
                if array.length == 0:
                    return False
                arraysInArrays = True
                for q in range(array.length):
                    if not isinstance(array.get(q), CBOR.Array):
                        arraysInArrays = False
                        break
                if arraysInArrays:
                    return True
                """ Where we are standing at the moment. """
                if (len(self.buffer) - self.start_of_line +
                    array.length +
                    2 +
                    len(array.to_diagnostic(False))) > 70:
                    return True
            return False

        def newlineAndIndent(self):
            if self.pretty_print:
                self.start_of_line = len(self.buffer)
                self.buffer += '\n'
                for i in range (self.indentation_level):
                    self.buffer += '  '

        def endList(self, notEmpty, endChar):
            self.indentation_level -= 1
            if notEmpty:
                self.newlineAndIndent()
            self.buffer += endChar

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
        """
        Convert unsigned integer to bytearray (but with a twist).
        """
        array = bytearray()
        while True:
            array += bytes([value & 0xff])
            value >>= 8
            if value == 0: break
        length = len(array)
        """
        Prepare for "int" encoding (1, 2, 4, 8). 
        Only 3, 5, 6, and 7 need an action.
        """
        while length < 8 and length > 2 and length != 4:
            array += bytes([0])
            length += 1 
        array.reverse() # Make it big endian.
        """
        Does this number qualify as a "bigint"?
        """
        if length <= 8:
            """
            Apparently not, encode it as "int".
            """
            if length == 1 and array[0] <= 23:
                return bytearray([array[0] | tag]) # Header-only int
            modifier = 24
            while True:
                length >>= 1
                if length == 0: break  
                modifier += 1
            return bytearray([tag | modifier]) + array
        """
        True "bigint".
        """
        return (bytearray([CBOR._TAG_BIG_UNSIGNED if tag == CBOR._MT_UNSIGNED
                          else CBOR._TAG_BIG_NEGATIVE]) + 
                CBOR._encode_string(CBOR._MT_BYTES, array))

    @staticmethod
    def _return_converted(float16_flag, value):
        if math.isfinite(CBOR._check_argument_type(value, 'float')):
            try:
                reduced = struct.unpack("!f", struct.pack("!f", value))[0]
                if float16_flag:
                    reduced = struct.unpack(
                        "!e", struct.pack("!e", reduced))[0]
            except OverflowError:
                CBOR._error(
                    "Not possible reducing {:g} into a \"{:s}\"".format(
                        value, "float16" if float16_flag else "float32"))
        else: reduced = value
        return CBOR.Float(reduced)

    @staticmethod
    def _int_range_check(value, min, max):
        if value < min or value > max:
            if min < 0 and max != 9007199254740991: max += 1
            bits = 0
            while max:
                max >>= 1
                bits += 1
            CBOR._range_error(("int" if min else "uint") + str(bits),
                              str(value))
        return value

    @staticmethod
    def _range_error(type, valueString):
        CBOR._error('Value out of range for "' + type + '": ' + valueString)

    @staticmethod
    def _check_argument_type(value, expected):
        if type(value).__name__ != expected:
            CBOR._error("Expected '" + expected +
                        "', got '" + type(value).__name__ + "'")
        return value
        
    @staticmethod
    def _check_int_argument(value):
        return CBOR._check_argument_type(value, 'int')
    
    @staticmethod
    def _check_bool_argument(value):
        return CBOR._check_argument_type(value, 'bool')

    @staticmethod
    def _check_bytes_argument(byte_string):  
        if type(byte_string).__name__ not in ['bytes', 'bytearray']:
            CBOR._error("Expected 'bytes' or 'bytearray' argument, got '" +
                        type(byte_string).__name__ + "'")
        return byte_string
    
    @staticmethod
    def _cbor_argument_check(object):
        if isinstance(object, CBOR._CborObject):
            return object
        CBOR._error("Expected CBOR.* argument, got '" + 
                    type(object).__name__ + "'")
    
    @staticmethod
    def _encode_16_bits(uint16):
        return bytes([uint16 >> 8, uint16 & 0xff])
    
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
    
    @staticmethod
    def _create_int(value, min, max):
        value = CBOR._check_int_argument(value)
        cbor_int = CBOR.Int(value)
        CBOR._int_range_check(value, min, max)
        return cbor_int

    @staticmethod
    def _bytes_to_uint(byte_array):
        value = 0
        for v in byte_array:
            value <<= 8
            value += v
        return value
    
    @staticmethod
    def _compare_byte_arrays(a, b):
        min_index = min(len(a), len(b))
        for i in range(min_index):
            diff = a[i] - b[i]
            if diff != 0:
                return diff
        return len(a) - len(b)

    @staticmethod
    def _check_time_parameters(instant, millis, utc):
        CBOR._check_argument_type(instant, "datetime")
        CBOR._check_bool_argument(millis)
        CBOR._check_bool_argument(utc)
        timestamp = datetime.datetime.timestamp(instant)
        if isinstance(timestamp, float):
            """
            For interoperability purposes, time objects are limitited
            to the UNIX "epoch", spanning from "1970-01-01T00:00:00Z"
            to "9999-12-31T23:59:59Z".
            """
            CBOR._check_time_range(timestamp)
            """
            The caller decides if precision beyond seconds is required.
            If only seconds are required, rounding is performed.
            """   
            if millis:
                timestamp = int(timestamp * 1000 + 0.5) / 1000.0 
                if int(timestamp) == timestamp:
                    timestamp = int(timestamp)
            else:
                timestamp = int(timestamp + 0.5)
        return timestamp
    
    @staticmethod    
    def _check_time_range(timestamp):
        if ((isinstance(timestamp, float) and not math.isfinite(timestamp)) or
            timestamp < 0 or timestamp > 253402300799):
                CBOR._error("Timestamp out of range: " + str(timestamp))
        return timestamp
    
    @staticmethod
    def _remove_trailing_zeros(date_string):
        if date_string.find(".") > 0:
            i = len(date_string)
            while i > 0:
                i -= 1
                if date_string[i] != "0": break
                date_string = date_string[0:i]
        return date_string
