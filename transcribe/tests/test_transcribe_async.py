import json
import pytest

from transcribe.tests.utils import TESTDOCS_DIR, write_response, get_audio_urls
import transcribe.transcribe_async as ta

TRANSCRIPTS_FILE = "transcripts.json"


@pytest.mark.deepgram
@write_response(TRANSCRIPTS_FILE)
def test_transcribe_urls_success():
    audio_urls = get_audio_urls()
    response = ta.transcribe_urls(audio_urls)

    return response


@pytest.fixture
def response():
    with open(TESTDOCS_DIR / TRANSCRIPTS_FILE, "r") as file:
        t = json.load(fp=file)
    return t


def test_transcribe_urls_contents(response):
    for _, transcript in response.items():
        assert "results" in transcript
        assert "captions" in transcript
