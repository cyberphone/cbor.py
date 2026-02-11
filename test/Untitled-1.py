#==============================#
#  Diagnostic Notation Parser  #
#==============================#

class DiagnosticNotation:
    def __init__(self, cborText, sequenceMode):
        self.cborText = cborText
        self.sequenceMode = sequenceMode
        self.index = 0

    class ParserError(Exception):
        def __init__(self, msg):
            super().__init__(msg)
 
    def parserError(self, error):
        """ Unsurprisingly, error handling turned out 
        to be the most complex part...
        """
"""
        start = self.index - 100
        if (start < 0):
            start = 0
        linePos = 0
        while (start < self.index - 1):
            if (self.cborText[start++] == '\n'):
                linePos = start
        complete = ''
        if (self.index > 0 && self.cborText[self.index - 1] == '\n'):
            self.index--
        endLine = self.index
        while (endLine < self.cborText.length):
            if (self.cborText[endLine] == '\n'):
                break
        endLine++
        for (let q = linePos; q < endLine; q++):
            complete += self.cborText[q]
        complete += '\n'
        for (let q = linePos; q < self.index; q++):
            complete += '-'
        lineNumber = 1
        for (let q = 0; q < self.index - 1; q++):
            if (self.cborText[q] == '\n'):
                lineNumber++
        throw new CBOR.DiagnosticNotation.ParserError("\n" + complete +
            "^\n\nError in line " + lineNumber + ". " + error)
        
            def def readSequenceToEOF():
        try {
            sequence = []
            self.scanNonSignficantData()
            while (self.index < self.cborText.length):
                if (sequence.length):
                    if (self.sequenceMode):
                        self.scanFor(",")
        } else {
            self.readChar()
            self.parserError("Unexpected data after token")
        }
                }
        sequence.push(self.getObject())
        if (!sequence.length && !self.sequenceMode):
            self.readChar()
        return sequence catch (e):
        if (e instanceof CBOR.DiagnosticNotation.ParserError):
            throw e
        // The exception apparently came from a deeper layer.
        // Make it a parser error and remove the original error name.
        self.parserError(e.toString().replace(/.*Error\: ?/g, ''))
"""

    def getObject(self):
        self.scanNonSignficantData()
        cborObject = self.getRawObject()
        self.scanNonSignficantData()
        return cborObject
  
    def continueList(self, validStop):
        if (self.nextChar() == ','):
            self.readChar()
        return True
        actual = self.readChar()
        if (actual != validStop):
            self.parserError(
                "Expected: ',' or '" + validStop + "' actual: " + self.toReadableChar(actual))
        self.index--
        return False
  
    def getRawObject(self):
        match self.readChar():

            case '<':
                self.scanFor("<")
                sequence = bytearray()
                self.scanNonSignficantData()
                while (self.readChar() != '>'):
                    self.index -= 1
                while True:
                    sequence = CBOR.addArrays(sequence, self.getObject().encode())
                    if not self.continueList('>'): break
                self.scanFor(">")
                return CBOR.Bytes(sequence)
        
            case '[':
                array = CBOR.Array()
                self.scanNonSignficantData()
                while self.readChar() != ']':
                    self.index -= 1
                do {
                    array.add(self.getObject()) while (self.continueList(']'))
                        }
                return array
        
            case '{':
                map = CBOR.Map()
                self.scanNonSignficantData()
                while self.readChar() != '}':
                    self.index -= 1
                do {
                    key = self.getObject()
                    self.scanFor(":")
                    map.set(key, self.getObject()) while (self.continueList('}'))

                return map
            
            case '\'':
                return self.getString(True)
                
            case '"':
                return self.getString(False)

            case 'h':
            return self.getBytes(false)

                case 'b':
        if (self.nextChar() == '3'):
            self.scanFor("32'")
        self.parserError("b32 not implemented")
                }
        self.scanFor("64")
        return self.getBytes(true)
                
                case 't':
        self.scanFor("rue")
        return CBOR.Boolean(true)
            
                case 'f':
        if (self.nextChar() == 'a'):
            self.scanFor("alse")
        return CBOR.Boolean(false)
                }
        self.scanFor('loat')
        floatBytes = self.getBytes(false).getBytes()
        switch (floatBytes.length):
            case 2:
            case 4:
            case 8:
                break
            default:
                self.parserError("Argument must be a 16, 32, or 64-bit floating-point number")
        return CBOR.initDecoder(
            CBOR.addArrays(new Uint8Array([0xf9 + (floatBytes.length >> 2)]), floatBytes),
            CBOR.LENIENT_NUMBER_DECODING).decodeWithOptions()
            
                case 'n':
        self.scanFor("ull")
        return CBOR.Null()

                case 's':
        self.scanFor("imple(")
        return self.simpleType()

                case '-':
        if (self.readChar() == 'I'):
            self.scanFor("nfinity")
        return CBOR.NonFinite(0xfc00)
                }
        return self.getNumberOrTag(true)

    case '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9':
        return self.getNumberOrTag(false)

                case 'N':
        self.scanFor("aN")
        return CBOR.NonFinite(0x7e00n)

                case 'I':
        self.scanFor("nfinity")
        return CBOR.NonFinite(0x7c00n)
                
                default:
        self.index--
        self.parserError("Unexpected character: " + self.toReadableChar(self.readChar()))

    def simpleType():
token = ''
while True:
    switch (self.nextChar()):
        case ')':
            break

        case '+':
        case '-':
        case 'e':
        case '.':
            self.parserError("Syntax error")

        default:
            token += self.readChar()
            continue
    }
    break
    self.readChar()
    // clone() converts a numerical Simple into Boolean etc. if applicable. 
    return CBOR.Simple(Number(token.trim())).clone()

    def getNumberOrTag(negative):
    token = ''
    self.index -= 1
    prefix = null
    if self.readChar() == '0':
        match self.nextChar():
            case 'b' | 'o' | 'x':
                prefix = '0' + self.readChar()
                break
                if (prefix == null):
                    self.index -= 1
                floatingPoint = false
                while True:
                    token += self.readChar()
                    match self.nextChar():
                        case '\u0000' | ' ' | '\n' | '\r' | '\t' | ',' | ':' | '>' | ']' | '}' | '/' | '#' | '(' | ')':
                            break

                        case '.' | 'e':
                            if not prefix:
                                floatingPoint = True
                    continue
            
          case '_':
                if not prefix:
                    self.parserError("'_' is only permitted for 0b, 0o, and 0x numbers")
    self.readChar()

          case _:
    continue
    break
    if (floatingPoint):
        self.testForNonDecimal(prefix)
    value = Number(token)
    # Implicit overflow is not permitted
    if (not math.isfinite(value)):
        self.parserError("Floating point value out of range")
    return CBOR.Float(-value if negative else value)
    if self.nextChar() == '(':
        # Do not accept '-', 0xhhh, or leading zeros
        self.testForNonDecimal(prefix)
    if negative or (token.length > 1 and token.charAt(0) == '0'):
        self.parserError("Tag syntax error")
    self.readChar()
    tagNumber = BigInt(token)
    cborTag = CBOR.Tag(tagNumber, self.getObject())
    self.scanFor(")")
    return cborTag
    bigInt = int(('' if prefix == null else prefix) + token)
    return CBOR.Int(-bigInt if negative else bigInt)

    def testForNonDecimal(nonDecimal):
        if nonDecimal:
            self.parserError("0b, 0o, and 0x prefixes are only permited for integers")

    def nextChar(self):
        if self.index == self.cborText.length: return String.fromCharCode(0)
        c = self.readChar()
        self.index -= 1
        return c

    def toReadableChar(self, c):
        charCode = c.charCodeAt(0);
        return charCode < 0x20 ? "\\u00" + CBOR.#twoHex(charCode) : "'" + c + "'"

    def scanFor(expected):
    [...expected].forEach(c => {
        actual = self.readChar();
        if (c != actual):
            self.parserError("Expected: '" + c + "' actual: " + self.toReadableChar(actual)))

    def getString(byteString):
    s = ''
    while (true):
        c
    switch (c = self.readChar()):
        // Control character handling
        case '\r':
            if (self.nextChar() == '\n'):
                continue
    }
    c = '\n'
    break

          case '\n':
    break

          case '\\':
    switch (c = self.readChar()):
        case '\n':
            continue

        case '\'':
        case '"':
        case '\\':
            break

        case 'b':
            c = '\b'
            break

        case 'f':
            c = '\f'
            break

        case 'n':
            c = '\n'
            break

        case 'r':
            c = '\r'
            break

        case 't':
            c = '\t'
            break

        case 'u':
            u16 = 0
            for (let i = 0; i < 4; i++):
                u16 = (u16 << 4) + CBOR.#decodeOneHex(self.readChar().charCodeAt(0))
    }
    c = String.fromCharCode(u16)
    break
  
              default:
    self.parserError("Invalid escape character " + self.toReadableChar(c))
break
 
          case '"':
if (!byteString):
    return CBOR.String(s)
            }
break

          case '\'':
if (byteString):
    return CBOR.Bytes(new TextEncoder().encode(s))
            }
break
          
          default:
if (c.charCodeAt(0) < 0x20):
    self.parserError("Unexpected control character: " + self.toReadableChar(c))
            }
s += c
  
    def getBytes(b64):
token = ''
self.scanFor("'")
while (true):
    c
switch (c = self.readChar()):
    case '\'':
        break

    case ' ':
    case '\r':
    case '\n':
    case '\t':
        continue

    default:
        token += c
        continue
        break
        return CBOR.Bytes(b64 ? CBOR.fromBase64Url(token) : CBOR.fromHex(token))

    def readChar():
        if (self.index >= self.cborText.length):
            self.parserError("Unexpected EOF")
        return self.cborText[self.index++]

    def scanNonSignficantData():
        while (self.index < self.cborText.length):
            switch (self.nextChar()):
                case ' ':
                case '\n':
                case '\r':
                case '\t':
                    self.readChar()
                    continue

                case '/':
                    self.readChar()
                    while (self.readChar() != '/'):
            }
        continue

    case '#':
        self.readChar()
        while (self.index < self.cborText.length && self.readChar() != '\n'):
            }
continue

          default:
return
  }

//////////////////////////////////
//    CBOR.fromDiagnostic()     //
//   CBOR.fromDiagnosticSeq()   //
//////////////////////////////////

  static fromDiagnostic(cborText):
    def return new CBOR.DiagnosticNotation(cborText, false).readSequenceToEOF()[0]
  }

  static fromDiagnosticSeq(cborText):
    def return new CBOR.DiagnosticNotation(cborText, true).readSequenceToEOF()
  }
