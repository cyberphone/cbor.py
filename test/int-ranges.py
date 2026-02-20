# Testing range-constrained integers
from org.webpki.cbor import CBOR
from assertions import assert_true, assert_false, fail, success, check_exception


def goodRun(type, value):
  bigFlag = type.find("64") > 0 or type.find("128") > 0
  wrapper = CBOR.decode(CBOR.Int(value).encode())
  test = 'assert_true("good", wrapper.get' + type + '() == ' + \
    str(value) + ')'
  eval(test)
  test = 'CBOR.Int.create' + type + '(' + str(value) + ')'
  eval(test)
  if value == 10:
    test = 'CBOR.Int.create' + type + '(' + str(value) +')'
    eval(test)

def badRun(type, value):
  wrapper = CBOR.decode(CBOR.Int(value).encode())
  test = 'wrapper.get' + type + '()'
  try:
    eval(test)
    fail("Should fail")
  except Exception as error:
    check_exception(error, "Value out of range")
  test = 'CBOR.Int.create' + type + '(' + str(value) + ')'
  try:
    eval(test)
    fail("Should fail")
  except Exception as error:
    check_exception(error, "Value out of range")

def innerTurn(type, signed, size):
  min_val = -(1 << size - 1) if signed else 0
  max_val = (1 << size - 1) - 1 if signed else (1 << size) - 1
  if size == 53:
    max_val = 0x1fffffffffffff
    min_val = -max_val
  goodRun(type, min_val)
  goodRun(type, max_val)
  goodRun(type, 10)
  badRun(type, max_val + 1)
  badRun(type, min_val - 1)

def oneTurn(size):
  innerTurn("_int" + str(size), True, size)
  if size != 53:
    innerTurn("_uint" + str(size), False, size)

oneTurn(8)
oneTurn(16)
oneTurn(32)
oneTurn(53)
oneTurn(64)
oneTurn(128)

success()
