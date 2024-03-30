import pathlib, json, os

"""
helper functions and variables for transcribe.
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
            with open(TESTDOCS_DIR / filename, "w") as file:
                json.dump(response, file, indent=2)

        return wrapper

    return inner


def get_audio_urls():
    with open(TESTDOCS_DIR / "sessions.json", "r") as file:
        sessions = json.load(fp=file)

    def format_pair(name: str, url_str: str):
        extension = os.path.splitext(name)[1]
        url = (
            f"https://insightflow-test.s3.us-east-2.amazonaws.com/{url_str}{extension}"
        )
        return (name, url)

    audio_urls = {
        name: url for name, url in map(format_pair, sessions.values(), sessions.keys())
    }

    return audio_urls
