from org.webpki.cbor import CBOR
import math
import struct
import io

def assert_true(text, expression):
  if not expression:
    raise Exception("Failed on: " + text)
  
def assert_false(text, expression):
  if expression:
    raise Exception("Failed on: " + text)
  
def fail(text):
  raise Exception("Failed on: " + text)

def check_exception(exception, expected, throw=True):
  if repr(exception).find(expected) >= 0:
    return True
  if throw:
    raise Exception("Expected '{:s}', got '{:s}'".format(expected, repr(exception)))
  return False

__name = ''
def success():
  print('Test ' + __name + ' was successful')

__count = 0

TESTS = [
]

for o in TESTS:
  __name = o[0]
  try:
    exec(o[1])
  except Exception:
    print("Failed '" + __name + "'")
    __count += 1
if (__count):
  print("***ERRORS*** " + str(__count))
else:
  print("SUCCESSFUL")
