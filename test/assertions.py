def assert_true(text, expression):
  if not expression:
    raise Exception("Failed on: " + text)
  
def assert_false(text, expression):
  if expression:
    raise Exception("Failed on: " + text)
  
def fail(text):
  raise Exception("Failed on: " + text)

def success():
  print("SUCCESSFUL")
