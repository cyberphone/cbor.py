#==============================#
#  Diagnostic Notation Parser  #
#==============================#

    class _DiagnosticNotation:
        def __init__(self, cbor_text, sequence_mode):
            self.cbor_text = cbor_text
            self.sequence_mode = sequence_mode
            self.index = 0

        class ParserError(Exception):
            def __init__(self, msg):
                super().__init__(msg)
    
        def parser_error(self, error):
            pass
            """ Unsurprisingly, error handling turned out 
            to be the most complex part...
            """
            start = self.index - 100
            if (start < 0):
                start = 0
            line_pos = 0
            while (start < self.index - 1):
                temp = start
                start += 1
                if (self.cbor_text[temp] == '\n'):
                    line_pos = start
            complete = ''
            if self.index > 0 and self.cbor_text[self.index - 1] == '\n':
                self.index -= 1
            end_line = self.index
            while end_line < len(self.cbor_text):
                if (self.cbor_text[end_line] == '\n'):
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
                if (self.cbor_text[q] == '\n'):
                    line_number += 1
                q += 1
            raise CBOR.DiagnosticNotation.ParserError("\n" + complete +
                "^\n\nError in line " + line_number + ". " + error)
        
        def read_sequence_to_eof(self):
            try:
                sequence = []
                self.scan_non_signficant_data()
                while self.index < len(self.cbor_text):
                    if len(sequence):
                        if (self.sequence_mode):
                            self.scan_for(",")
                    else:
                        self.read_char()
                        self.parser_error("Unexpected data after token")
                    sequence.push(self.get_object())
                if not len(sequence) and not self.sequence_mode:
                    self.read_char()
                return sequence 
            except CBOR.DiagnosticNotation.ParserError as e:
                CBOR._error(repr(e))
            # The exception apparently came from a deeper layer.
            # Make it a parser error and remove the original error name.
            # self.parser_error(repr(e).replace(/.*Error\: ?/g, ''))
            self.parser_error(repr(e))

        def get_object(self):
            self.scan_non_signficant_data()
            cbor_bbject = self.get_raw_object()
            self.scan_non_signficant_data()
            return cbor_bbject
    
        def continue_list(self, valid_stop):
            if (self.next_char() == ','):
                self.read_char()
                return True
            actual = self.read_char()
            if (actual != valid_stop):
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
                            if self.continue_list('>'): break
                    self.scan_for(">")
                    return CBOR.Bytes(sequence)
            
                case '[':
                    array = CBOR.Array()
                    self.scan_non_signficant_data()
                    while self.read_char() != ']':
                        self.index -= 1
                        while True:
                            array.add(self.get_object())
                            if self.continue_list(']'): break
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
                            if self.continue_list('}'): break
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
                    if (self.next_char() == 'a'):
                        self.scan_for("alse")
                        return CBOR.Boolean(False)
                    self.scan_for('loat')
                    float_bytes = self.get_bytes(False).get_bytes()
                    if len(float_bytes) not in [2, 4, 8]:
                        self.parser_error(
                            "Argument must be a 16, 32, or 64-bit floating-point number")
                    return CBOR.init_decoder(
                        IObytes(bytes([0xf9 + (float_bytes.length >> 2)]) + float_bytes,
                        CBOR.LENIENT_NUMBER_DECODING,
                        100)).decode_with_options()
                
                case 'n':
                    self.scan_for("ull")
                    return CBOR.Null()

                case 's':
                    self.scan_for("imple(")
                    return self.simple_type()

                case '-':
                    if (self.read_char() == 'I'):
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
            return CBOR.Simple(int(token.trim())).clone()

        def get_number_or_tag(self, negative):
            token = ''
            self.index -= 1
            prefix = None
            if self.read_char() == '0' and self.next_char() in ['b' , 'o' , 'x']:
                prefix = '0' + self.read_char()
            if not prefix:
                self.index -= 1
            floating_point = False
            while True:
                token += self.read_char()
                match self.next_char():
                    case '\h00' | ' ' | '\n' | '\r' | '\t' | ',' | ':' |\
                        '>' | ']' | '}' | '/' | '#' | '(' | ')':
                        break

                    case '.' | 'e':
                        if not prefix:
                            floating_point = True
                    
                    case '_':
                        if not prefix:
                            self.parser_error("'_' is only permitted for 0b, 0o, and 0x numbers")
                        self.read_char()

                if (floating_point):
                    self.test_for_non_decimal(prefix)
                    value = float(token)
                    # Implicit overflow is not permitted
                    if not math.isfinite(value):
                        self.parser_error("Floating point value out of range")
                    return CBOR.Float(-value if negative else value)
                if self.next_char() == '(':
                    # Do not accept '-', 0xhhh, or leading zeros
                    self.test_for_non_decimal(prefix)
                    if negative or (token.length > 1 and token.charAt(0) == '0'):
                        self.parser_error("Tag syntax error")
                    self.read_char()
                    tag_number = int(token)
                    cbor_tag = CBOR.Tag(tag_number, self.get_object())
                    self.scan_for(")")
                    return cbor_tag
                bigInt = int(('' if prefix == null else prefix) + token)
                return CBOR.Int(-bigInt if negative else bigInt)

        def test_for_non_decimal(self, non_decimal):
            if non_decimal:
                self.parser_error("0b, 0o, and 0x prefixes are only permited for integers")

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
            if (c != actual):
                self.parser_error("Expected: '" + c + "' actual: " + 
                                self.to_readable_char(actual))

        def get_string(self, byteString):
            s = ''
            while True:
                c = self.read_char()
                match c:
                    # Control character handling
                    case '\r':
                        if (self.next_char() == '\n'):
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
            while (True):
                c = self.read_char()
                match c:
                    case '\'':
                        return CBOR.Bytes(
                            base64.urlsafe_b64decode(token) if
                                b64 else bytes.fromHex(token))

                    case ' ' | '\r' | '\n' | '\t':
                        continue

                    case _:
                        token += c
                        continue

        def read_char(self):
            if self.index >= len(self.cbor_text):
                self.parser_error("Unexpected EOF")
            self.index += 1
            return self.cbor_text[self.index]

        def scan_non_signficant_data(self):
            while (self.index < self.cbor_text.length):
                match (self.next_char()):
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
                        while (self.index < self.cbor_text.length and self.read_char() != '\n'):
                            """ No-Op """
                        continue

                    case _:
                        return

    #################################
    #     CBOR.fromDiagnostic()     #
    #    CBOR.fromDiagnosticSeq()   #
    #################################

    @staticmethod
    def from_diagnostic(cborText):
        return CBOR.DiagnosticNotation(cborText, 
                                       False).readSequenceToEOF()[0]

    @staticmethod
    def from_diagnostic_seq(cborText):
        return CBOR.DiagnosticNotation(cborText, 
                                       True).readSequenceToEOF()

