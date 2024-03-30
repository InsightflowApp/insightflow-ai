import db.user_projects as up
import json
import pathlib

"""
make the testing items for transcribe/tests.

currently only makes sessions.json.

future work:
"""

docs_dir = pathlib.Path(__file__).parent
# gamma template research
PROJECT = up.get_project_by_id(up.test_project_id)


def main():
    with open(docs_dir / "sessions.json", "w") as file:
        json.dump(PROJECT["sessions"], fp=file)


if __name__ == "__main__":
    main()
