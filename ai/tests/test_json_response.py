from ai.json_response import *
from collections.abc import Callable
import json
import pytest


def write_response(filename: str):

  def inner(func):

    def wrapper(*args, **kwargs):
      response = func(*args, **kwargs)
      with open(filename, 'w') as file:
        json.dump(response, file, indent=2)

    return wrapper
  
  return inner

@write_response("example_response.json")
def test_md_to_json():
  text = ""

  with open("ai/tests/example_response.md", 'r') as file:
    text = file.read()

  response = md_to_json(text)

  assert response_format_correct(response)

  question_found: bool = False
  for question in response["questions"]:
    if question["question"] == "What factors initially motivated individuals to pursue studies in Computer Science?":
      question_found = True
      assert len(question["themes"]) == 3
      for theme in question["themes"]:
        if theme["theme"] == "Interest in Technology and Computers":
          # assert len(theme["quotes"]) == theme["count"]
          assert len(theme["quotes"]) == 3
      

      break

  assert question_found


def _format_correct(model: BaseModel, nested_fields : dict[str, BaseModel]) -> Callable:
  def check(response: dict) -> bool:

    for field in model.__fields__.keys():
      assert field in response
    
    for nested_field, nested_call in nested_fields.items():
      for item in response[nested_field]:
        assert nested_call(item)
    
    return True
  
  return check

# checking pydantic fields
quote_format_correct : Callable = _format_correct(Quote, {})
theme_format_correct : Callable = _format_correct(Theme, {"quotes": quote_format_correct})
question_format_correct : Callable = _format_correct(Question, {"themes": theme_format_correct})
response_format_correct : Callable = _format_correct(Finding, {"questions": question_format_correct})
