# Simple "encoder" API
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success

class XYZEncoder:

  COUNTER     = CBOR.Int(1)
  TEMPERATURE = CBOR.Int(2)
  GREETING    = CBOR.Int(3)

  def __init__(self):
    self._map = CBOR.Map()

  def set_counter(self, intVal):
    self._map.set(XYZEncoder.COUNTER, CBOR.Int.create_uint8(intVal))
    return self

  def set_temperature(self, floatVal):
    self._map.set(XYZEncoder.TEMPERATURE, CBOR.Float(floatVal))
    return self

  def set_greeting(self, stringVal):
    self._map.set(XYZEncoder.GREETING, CBOR.String(stringVal))
    return self

  def build(self):
    assert_true("incomplete", self._map.length == 3)
    return self._map.encode()

# Using the "builder" pattern:
cbor = (XYZEncoder()          
      .set_counter(2)           
      .set_greeting('Hi!')      
      .set_temperature(53.0001) 
      .build())

assert_true("bad code", cbor.hex() == 'a3010202fb404a800346dc5d640363486921')

success()
