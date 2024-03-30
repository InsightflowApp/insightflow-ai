import json, pytest

from ai.tests.utils import TESTDOCS_DIR
from ai.mvp import quick_test, map_reduce

with open(TESTDOCS_DIR / "mvp_project.json", "r") as file:
    TEST_PROJECT = json.load(fp=file)

RESPONSE_FILE = "mvp_response.md"


@pytest.mark.skip(reason="unnecessary call if we know API is working")
@pytest.mark.ai
def test_quick_test():
    response = quick_test(country="Australia")
    assert "Canberra" in response


@pytest.mark.ai
def test_get_map_reduce():
    response = map_reduce(TEST_PROJECT["questions"], TEST_PROJECT["transcripts"])

    with open(TESTDOCS_DIR / RESPONSE_FILE, "w") as file:
        print(response, file=file)


def test_map_reduce():
    with open(TESTDOCS_DIR / RESPONSE_FILE, "r") as file:
        data = file.read()

    assert type(data) is str

    # TODO more testing
