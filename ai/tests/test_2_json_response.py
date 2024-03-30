from collections.abc import Callable
import json, pathlib, pytest

from ai.tests.utils import TESTDOCS_DIR, write_response
from ai.json_response import *

JSON_RESPONSE_FILE = "json_response.json"

@pytest.mark.ai
@write_response(JSON_RESPONSE_FILE)
def test_md_to_json_success() -> dict:
  """write the contents of a markdown response into json."""

  with open(TESTDOCS_DIR / "json_response.md", 'r') as file:
    text = file.read()

  response: dict = md_to_json(text)

  return response


@pytest.fixture
def response():
  with open(TESTDOCS_DIR / JSON_RESPONSE_FILE, 'r') as file:
    response = json.load(fp=file)
  return response


def test_md_to_json_format(response):
  """test the contents of a markdown response into json."""
  assert response_format_correct(response)


@pytest.mark.skip(reason="outdated")
def test_md_to_json_content(response):
  """test the contents of a markdown response according to its question content"""
  question_found: bool = False
  for question in response["questions"]:
    if question["question"] == "What are users' feedback on gamma templates?":
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
