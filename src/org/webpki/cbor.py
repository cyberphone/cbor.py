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

import struct
import math
import io

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

        def _check_type_get_value(self, expected):
            if type(self).__name__ != expected:
                CBOR._error("Expected '" + 'CBOR.' + expected +
                            "', got 'CBOR." + type(self).__name__  + "'")
            self._read_flag = True
            return self._get()

        def get_big_integer(self):
            return self._check_type_get_value('Int')
        
        def _get_checked_int(self, min, max):
            return CBOR._int_range_check(self.get_big_integer(), min, max)

        def get_int8(self):
            return self._get_checked_int(-0x80, 0x7f)

        def get_uint8(self):
            return self._get_checked_int(0, 0xff)

        def get_int16(self):
            return self._get_checked_int(-0x8000, 0x7fff)

        def get_uint16(self):
            return self._get_checked_int(0, 0xffff)

        def get_int32(self):
            return self._get_checked_int(-0x80000000, 0x7fffffff)

        def get_uint32(self):
            return self._get_checked_int(0, 0xffffffff)

        def get_int53(self):
            return self._get_checked_int(-9007199254740991, 9007199254740991)

        def get_int64(self):
            return self._get_checked_int(-0x8000000000000000,
                                         0x7fffffffffffffff)

        def get_uint64(self):
            return self._get_checked_int(0, 0xffffffffffffffff)

        def get_int128(self):
            return self._get_checked_int(-0x80000000000000000000000000000000,
                                         0x7fffffffffffffffffffffffffffffff)

        def get_uint128(self):
            return self._get_checked_int(0, 0xffffffffffffffffffffffffffffffff)
        
        def get_float64(self):
            return self._check_type_get_value('Float')
        
        def get_string(self):
            return self._check_type_get_value('String')
        
        def get_bytes(self):
            return self._check_type_get_value('Bytes')

        def get_boolean(self):
            return self._check_type_get_value('Boolean')

        def is_null(self):
            if type(self).__name__ == 'Null':
                self._read_flag = True
                return True
            return False
        
        def get_non_finite64(self):
            return self._check_type_get_value('NonFinite')

        def encode(self):
            return self._internal_encode()
        
        def check_for_unread(self):
            if not self._read_flag:
                CBOR._error("Not read: " + type(self).__name__)

        def scan(self):
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

    ##########################
    #       CBOR.Int         #
    ##########################
    class Int(_CborObject):
        def __init__(self, value):
            super().__init__()
            self._value = CBOR._check_int_argument(value)

        @classmethod
        def create_int8(cls, value):
            return CBOR._create_int(value, -0x80, 0x7f)

        @classmethod
        def create_uint8(cls, value):
            return CBOR._create_int(value, 0, 0xff)

        @classmethod
        def create_int16(cls, value):
            return CBOR._create_int(value, -0x8000, 0x7fff)

        @classmethod
        def create_uint16(cls, value):
            return CBOR._create_int(value, 0, 0xffff)

        @classmethod
        def create_int32(cls, value):
            return CBOR._create_int(value, -0x80000000, 0x7fffffff)

        @classmethod
        def create_uint32(cls, value):
            return CBOR._create_int(value, 0, 0xffffffff)

        @classmethod
        def create_int53(cls, value):
            return CBOR._create_int(value, 
                                    -9007199254740991, 
                                    9007199254740991)

        @classmethod
        def create_int64(cls, value):
            return CBOR._create_int(value, 
                                    -0x8000000000000000,
                                    0x7fffffffffffffff)

        @classmethod
        def create_uint64(cls, value):
            return CBOR._create_int(value, 0, 0xffffffffffffffff)
            
        @classmethod
        def create_int128(cls, value):
            return CBOR._create_int(value, 
                                    -0x80000000000000000000000000000000,
                                    0x7fffffffffffffffffffffffffffffff)

        @classmethod
        def create_uint128(cls, value):
            return CBOR._create_int(value,
                                    0, 0xffffffffffffffffffffffffffffffff)

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
                f64bin = CBOR._bytes_to_int(f64b)
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
            nf = CBOR.NonFinite(CBOR._bytes_to_int(struct.pack('!d', value)))
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
            self._objects.append(object)
            return self
        
        def get(self, index):
            return self._objects[self._index_check(
                index, len(self._objects) - 1)]

        def _index_check(self, index, max):
            if CBOR._check_int_argument(index) > max or index < 0:
                CBOR._error("Index out of range: " + str(index))
            return index
        
        def _internal_encode(self):
            encoded = CBOR._generic_header(CBOR._MT_ARRAY, len(self._objects))
            for object in self._objects:
                encoded += object._internal_encode()
            return encoded
        
        def _internal_to_string(self, cbor_printer):
            if cbor_printer.arrayFolding(self):
                cbor_printer.beginList('[')
                notFirst = False
                for object in self._objects:
                    if notFirst:
                        cbor_printer.append(',')
                    notFirst = True
                    cbor_printer.newlineAndIndent()
                    object._internal_to_string(cbor_printer)
                cbor_printer.endList(notFirst, ']')
            else:
                cbor_printer.append('[')
                notFirst = False
                for object in self._objects:
                    if notFirst:
                        cbor_printer.append(',').space()
                    notFirst = True
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
            # self._immutableTest();
            new_entry = CBOR._Entry(key, object)
            # self.#makeImmutable(key);
            insert_index = len(self._entries)
            if insert_index:
                end_index = insert_index - 1
                if self._pre_sorted_keys:
                    """ Normal case for deterministic decoding. """
                    if (self._entries[end_index]._compare_and_test(new_entry)):
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

        """
        update(key, object, existing):
        CBOR.#checkArgs(arguments, 3);
        self._immutableTest();
        entry = self._lookup(key, existing);
        previous;
        if (entry):
            previous = entry.object;
            entry.object = CBOR.#cborArgumentCheck(object);
        } else {
            previous = null;
            self.set(key, object);
        return previous;
        """

        """
        merge(map):
        CBOR.#checkArgs(arguments, 1);
        self._immutableTest();
        if (!(map instanceof CBOR.Map)):
            CBOR._error("Argument must be of type CBOR.Map");
        map._entries.forEach(entry => {
            self.set(entry.key, entry.object);
        });
        return self
        """

        def get(self, key):
            self._read_flag = True
            return self._lookup(key, True)._object

        """
        getConditionally(key, defaultObject):
        CBOR.#checkArgs(arguments, 2);
        entry = self._lookup(key, false);
        // Note: defaultValue may be 'null'
        defaultObject = defaultObject ? CBOR.#cborArgumentCheck(defaultObject) : null;
        return entry ? entry.object : defaultObject;

        getKeys():
        keys = [];
        self._entries.forEach(entry => {
            keys.push(entry.key);
        });
        return keys;

        remove(key):
        CBOR.#checkArgs(arguments, 1);
        self._immutableTest();
        targetEntry = self._lookup(key, true);
        self._entries.splice(self._lastLookup, 1);
        return targetEntry.object;

        _getLength():
        return len(self._entries);

        containsKey(key):
        CBOR.#checkArgs(arguments, 1);
        return self._lookup(key, false) != null;
        """

        def encode(self):
            encoded = CBOR._generic_header(CBOR._MT_MAP, len(self._entries))
            for entry in self._entries:
                encoded += entry._encoded_key + entry._object.encode()
            return encoded

        def _internal_to_string(self, cbor_printer):
            notFirst = False
            cbor_printer.beginList("{")
            for entry in self._entries:
                if notFirst:
                    cbor_printer.append(",")
                notFirst = True
                cbor_printer.newlineAndIndent()
                entry._key._internal_to_string(cbor_printer)
                cbor_printer.append(":").space()
                entry._object._internal_to_string(cbor_printer)
            cbor_printer.endList(notFirst, "}")

        def set_sorting_mode(self, pre_sorted_keys):
            # CBOR.#checkArgs(arguments, 1);
            self._pre_sorted_keys = pre_sorted_keys
            return self

        """
        #makeImmutable(object):
        object._immutableFlag = true;
        if (object instanceof CBOR.Map):
            object.getKeys().forEach(key => {
            self.#makeImmutable(object.get(key));
            });
        } else if (object instanceof CBOR.Array):
            object.toArray().forEach(value => {
            self.#makeImmutable(value);
            });
        """

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
            if (diff == 0):
                CBOR._error("Duplicate key: " + str(self._key))
            return diff > 0

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
                """ Check that the syntax matches a non-finite number. """
                match len(self._ieee754):
                    case 2: exponent = 0x7c00
                    case 4: exponent = 0x7f800000
                    case 8: exponent = 0x7ff0000000000000
                    case _: self._bad_value()
                if (value & exponent) != exponent: self._bad_value()
                """ All is good, now apply "preferred serialization". """
                sign = self._ieee754[0] > 0x7f
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

        @classmethod
        def create_payload(cls, payload):
            CBOR._check_int_argument(payload)
            if (payload & 0x1fffffffffffff) != payload:
                CBOR._error("Payload out of range: " + payload)
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
    
        def _getLength(self):
            return len(self._ieee754)
    
        def _get(self):
            match len(self._ieee754):
                case 2: return self._to_non_finite64(10)
                case 4: return self._to_non_finite64(23)
            return self._value

        """
        def _getValue():
            return self._value
        """

#======================#  
#       Decoding       #
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
                CBOR._error("Exceeded set limit: max_length={:n}".format(self._max_length))
    
        def _eof_error(self):
            CBOR._error("Malformed CBOR, trying to read past EOF")

        def enter_level(self):
            self._nesting_level += 1
            if (self._nesting_level > self._max_nesting_level):
                CBOR._error("Structure nesting level exceeding: " + self._max_nesting_level)


        def set_max_nesting_level(self, max_level):
            self._max_nesting_level = CBOR._check_int_argument(max_level)
            return self

        def _read_byte(self):
            one_byte = self._cbor_stream.read(1)
            if not one_byte:
                if self._sequence_mode and self._at_first_byte:
                    return None
                self._eof_error()
            self._at_first_byte = False
            self._out_of_limit_test(1)
            return one_byte[0]

        def _read_bytes(self, length):
            if not length:
                return bytes([0]) # Python fix
            self._out_of_limit_test(length)
            byte_string = self._cbor_stream.read(length)
            if not byte_string or len(byte_string) < length:
                self._eof_error()
            return byte_string

        def _unsupported_tag(self, tag):
            CBOR._error("Unsupported tag: 0x{:02x}".format(tag))

        def _print_float_det_err(self, decoded):
            CBOR._error(
                "Non-deterministic encoding of floating-point number: " +
                "{:2x}{:s}".format(
                    CBOR._SIMPLE_FLOAT16 + (len(decoded) >> 2),
                    decoded.hex()))

        def _decode_float(self, length, mask, prefix):
            decoded = self._read_bytes(length)
            value = CBOR._bytes_to_int(decoded)
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
                            "Non-deterministic \"bigint\" object: " +
                            "{:02x}{:s}".format(tag, byte_array.hex()))
                    value = CBOR._bytes_to_int(byte_array)
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
            if (n > 27):
                self._unsupported_tag(tag)
            if (n > 23):
                """ For 1, 2, 4, and 8 byte N. """
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
                    CBOR._error("Non-deterministic length/count encoding " +
                                "for tag: 0x{:02x}".format(tag))
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
                    """ Programmatically added elements sort automatically. """
                    return cborMap.set_sorting_mode(False)

                case _:
                    self._unsupported_tag(tag)

        def decodeWithOptions(self):
            self._at_first_byte = True
            object = self._get_object()
            if (self._sequence_mode):
                if (self._at_first_byte):
                    return None
            elif (self._byte_count < self.maxLength):
                CBOR._error("Unexpected data encountered after CBOR object")
            return object

        def get_byte_count(self):
            return self._byte_count

    @classmethod
    def decode(cls, cbor_bytes):
        CBOR._check_bytes_argument(cbor_bytes)
        return CBOR.init_decoder(io.BytesIO(cbor_bytes), 
                                 0, len(cbor_bytes)).decode_with_options()

    @classmethod
    def init_decoder(cls, cbor_stream, options, max_length):
        return CBOR._Decoder(cbor_stream, options, max_length)
    
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
            if (self.pretty_print):
                self.buffer += ' '

        def arrayFolding(self, array):
            if (self.pretty_print):
                if array.length == 0:
                    return False
                arraysInArrays = True
                for q in range(0, array.length):
                    if not isinstance(array.get(q), CBOR.Array):
                        arraysInArrays = False
                        break
                if (arraysInArrays):
                    return True
                """ Where we are standing at the moment. """
                if (len(self.buffer) - self.start_of_line +
                    array.length +
                    2 +
                    (len(array.to_diagnostic(False)) > 70)):
                    return True
            return False

        def newlineAndIndent(self):
            if (self.pretty_print):
                self.start_of_line = len(self.buffer)
                self.buffer += '\n'
                for i in range (self.indentation_level):
                    self.buffer += '  '

        def endList(self, notEmpty, endChar):
            self.indentation_level -= 1
            if (notEmpty):
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
        """ Convert unsigned integer to bytearray (but with a twist). """
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
        """ Make big endian. """
        array.reverse()
        """ Does this number qualify as a "bigint"? """
        if length <= 8:
            """ Apparently not, encode it as "int". """
            if length == 1 and array[0] <= 23:
                return bytearray([array[0] | tag])
            modifier = 24
            while True:
                length >>= 1
                if length == 0: break  
                modifier += 1
            return bytearray([tag | modifier]) + array
        """ True "bigint". """
        return (bytearray([CBOR._TAG_BIG_UNSIGNED if tag == CBOR._MT_UNSIGNED
                          else CBOR._TAG_BIG_NEGATIVE]) + 
                CBOR._encode_string(CBOR._MT_BYTES, array))

    @staticmethod
    def _return_converted(float16_flag, value):
        type = "float16" if float16_flag else "float32"
        if math.isfinite(CBOR._check_argument_type(value, 'float')):
            try:
                reduced = struct.unpack("!f", struct.pack("!f", value))[0]
                if float16_flag:
                    reduced = struct.unpack(
                        "!e", struct.pack("!e", reduced))[0]
            except OverflowError:
                CBOR._error(
                    "Not possible reducing {:g} into a \"{:s}\"".format(
                        value, type))
        else: reduced = value
        return CBOR.Float(reduced)

    @staticmethod
    def _int_range_check(value, min, max):
        if (value < min or value > max):
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
        CBOR._error("Expected CBOR.* argument, got '" + type(object).__name__ + "'")
    
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
    def _bytes_to_int(byte_array):
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

