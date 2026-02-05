from org.webpki.cbor import CBOR

def assert_true(text, expression):
  if not expression:
    raise Exception("Failed on: " + text)
  
def assert_false(text, expression):
  if expression:
    raise Exception("Failed on: " + text)
  
def fail(text):
  raise Exception("Failed on: " + text)

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
