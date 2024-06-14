from db import db_connect as dbc
from bson.objectid import ObjectId

userDB = "User"
projectDB = "Project"
findingDB = "Finding"
transcriptDB = "Transcript"

# for testing
test_project_id = "6607464037ce70af1e36a4e1"


def get_user_project_ids(username: str):
    dbc.connect_db()

    user_filt = {"username": username}

    user = dbc.fetch_one(userDB, user_filt)

    return user["project"]


def get_project_by_id(id: str):
    """
    project fields:
    ```py
      _id : ObjectID
      projectName : str
      timeUpdated : str
      sessions : obj[url_extension: str, video_name: str]
      # sessions : array[obj[video_name: str, video_id: str, transcript_id: str]]
      questions : array[str]
      _class : str
    ```
    """
    dbc.connect_db()
    project_filter = {"_id": ObjectId(id)}

    project = dbc.fetch_one(projectDB, project_filter)

    return project


def update_project_status(
    id: str,
    status_num: int,
    findings_id: str | None = None,
    sessions: list[dict[str, str]] | None = None,
):
    dbc.connect_db()
    status = {"projectStatus": status_num}
    if findings_id is not None:
        status["findingsId"] = findings_id
    if sessions is not None:
        status["sessions"] = sessions

    return dbc.update_doc(projectDB, {"_id": ObjectId(id)}, status)


def get_user_project(username: str, project_index: int):
    """
    project fields:
    ```py
      _id : ObjectID
      projectName : str
      timeUpdated : str
      sessions : array[obj[video_name: str, video_id: str, transcript_id: str]]
      questions : array[str]
      _class : str
    ```
    """
    dbc.connect_db()
    projects = get_user_project_ids(username)

    project_filter = {"_id": ObjectId(projects[project_index])}

    project = dbc.fetch_one(projectDB, project_filter)

    return project


def insert_findings(findings: dict):
    dbc.connect_db()
    return dbc.insert_one(findingDB, findings)


def insert_transcript(data: dict):
    dbc.connect_db()
    return dbc.insert_one(transcriptDB, data)


def get_transcript_by_vid_id(id: str):
    dbc.connect_db()
    return dbc.fetch_one(transcriptDB, {"video_id": id})


def get_transcript(id: str):
    dbc.connect_db()
    return dbc.fetch_one(transcriptDB, {"_id": ObjectId(id)})
