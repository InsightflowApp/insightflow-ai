import pathlib, json, os
"""
helper functions and variables for AI.
"""

TESTDOCS_DIR = pathlib.Path(__file__).parent / "docs"


def write_response(filename: os.PathLike):
  """
  decorator to write a response to a file in testdocs_dir.

  usage:
  ```python
  @write_response("file.txt")
  def function_with_return_value_to_write() -> dict:
    ...
  ```
  """

  def inner(func):

    def wrapper(*args, **kwargs):
      # dict-like
      response = func(*args, **kwargs)
      with open(TESTDOCS_DIR / filename, 'w') as file:
        json.dump(response, file, indent=2)

    return wrapper
  
  return inner
