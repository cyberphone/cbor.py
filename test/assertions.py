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

def success():
  print("SUCCESSFUL")
