from langchain_core.pydantic_v1 import BaseModel
from collections.abc import Callable
import json, pytest

from ai.tests.utils import TESTDOCS_DIR, write_response
from ai.json_response import (
    md_to_json,
    Quote,
    Theme,
    Question,
    Finding,
    match,
    find_times,
)

from db import user_projects as up

JSON_RESPONSE_FILE = "json_response.json"


@pytest.fixture()
def transcript():
    return {
        "paragraphs": {
            "paragraphs": [
                {
                    "sentences": [
                        {"text": "Mhmm.", "start": 1592.44, "end": 1592.76},
                        {"text": "Yeah.", "start": 1592.76, "end": 1593.0},
                        {"text": "And we will", "start": 1593.0, "end": 1593.5599},
                    ],
                    "start": 1592.44,
                    "end": 1593.5599,
                    "num_words": 5,
                    "speaker": 0,
                },
                {
                    "sentences": [
                        {"text": "Okay.", "start": 1593.7999, "end": 1594.2999}
                    ],
                    "start": 1593.7999,
                    "end": 1594.2999,
                    "num_words": 1,
                    "speaker": 1,
                },
                {
                    "sentences": [
                        {
                            "text": "Some new features that are, like, for user to test some prototype or but a new features.",
                            "start": 1594.695,
                            "end": 1600.615,
                        },
                        {
                            "text": "So, yeah, glad to hear your feedback on that in the future.",
                            "start": 1600.615,
                            "end": 1603.995,
                        },
                    ],
                    "start": 1594.695,
                    "end": 1603.995,
                    "num_words": 29,
                    "speaker": 0,
                },
            ]
        }
    }


def test_match(transcript):
    # missing case of a partial end match
    s0_start = transcript["paragraphs"]["paragraphs"][0]["sentences"][2]
    s1_nomatch = transcript["paragraphs"]["paragraphs"][1]["sentences"][0]
    s2_partialmatch = transcript["paragraphs"]["paragraphs"][2]["sentences"][0]
    s3_endmatch = transcript["paragraphs"]["paragraphs"][2]["sentences"][1]

    Q_START = 4  # quote starts 4 chars into s0_start ("we will...")
    q = (" ".join([s0_start["text"], s2_partialmatch["text"], s3_endmatch["text"]]))[
        Q_START:
    ]
    print(f"{q=}")
    quote = {"quote": q}

    assert (0, -1.0, 0.0) == match(0, quote, s1_nomatch)

    first_cursor = len(s0_start["text"]) - Q_START + 1
    assert (
        first_cursor,
        s0_start["start"],
        0.0,
    ) == match(0, quote, s0_start)

    second_cursor = first_cursor + len(s2_partialmatch["text"]) + 1
    assert (
        second_cursor,
        s0_start["start"],
        0.0,
    ) == match(first_cursor, quote, s2_partialmatch, s0_start["start"])

    third_cursor = second_cursor + len(s3_endmatch["text"])
    assert (
        third_cursor,
        s0_start["start"],
        s3_endmatch["end"],
    ) == match(second_cursor, quote, s3_endmatch, s0_start["start"])


def test_find_times(monkeypatch, transcript):
    monkeypatch.setattr(up, "get_transcript", lambda _: transcript)
    ps = transcript["paragraphs"]["paragraphs"]
    q0 = ps[0]["sentences"][2]
    q1 = ps[2]["sentences"][0]
    q2 = ps[2]["sentences"][1]
    assert (q0["start"], q2["end"], 0) == find_times(
        {"quote": (" ".join([q0["text"], q1["text"], q2["text"]])), "transcript_id": ""}
    )


@pytest.mark.ai
@write_response(JSON_RESPONSE_FILE)
def test_md_to_json_success() -> dict:
    """write the contents of a markdown response into json."""

    with open(TESTDOCS_DIR / "json_response.md", "r") as file:
        text = file.read()

    response: dict = md_to_json(text)

    return response


@pytest.fixture
def response():
    with open(TESTDOCS_DIR / JSON_RESPONSE_FILE, "r") as file:
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


def _format_correct(model: BaseModel, nested_fields: dict[str, BaseModel]) -> Callable:
    def check(response: dict) -> bool:

        for field in model.__fields__.keys():
            assert field in response

        for nested_field, nested_call in nested_fields.items():
            for item in response[nested_field]:
                assert nested_call(item)

        return True

    return check


# checking pydantic fields
quote_format_correct: Callable = _format_correct(Quote, {})
theme_format_correct: Callable = _format_correct(
    Theme, {"quotes": quote_format_correct}
)
question_format_correct: Callable = _format_correct(
    Question, {"themes": theme_format_correct}
)
response_format_correct: Callable = _format_correct(
    Finding, {"questions": question_format_correct}
)
