import db.user_projects as up
import json
import pathlib

"""
make the testing items for ai/tests.

currently only makes mvp_project.json.

future work:
json_response.md
"""

docs_dir = pathlib.Path(__file__).parent
# AI TEST gamma
PROJECT = up.get_project_by_id(up.test_project_id)


def main():
    test_obj = dict()
    test_obj["questions"] = PROJECT["questions"]
    test_obj["transcripts"] = get_transcripts()

    with open(docs_dir / "mvp_project.json", "w") as file:
        json.dump(test_obj, fp=file, indent=2)


def get_transcripts():
    """
    gets transcripts corresponding to sessions
    """
    transcripts: list[str] = list()
    for id in PROJECT["sessions"].keys():
        transcript = up.get_transcript_by_vid_id(id)
        transcripts.append(
            f"Transcript_id: {str(transcript['_id'])}\n\n" + transcript["captions"]
        )

    return transcripts


if __name__ == "__main__":
    main()
