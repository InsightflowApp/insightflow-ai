from db import db_connect as dbc
from bson.objectid import ObjectId

userDB = 'User'
projectDB = 'Project'
findingDB = 'Finding'
transcriptDB = 'Transcript'

def get_user_project_ids(username : str):
  dbc.connect_db()

  user_filt = {'username': username}

  user = dbc.fetch_one(userDB, user_filt)

  return user['project']


def get_project_by_id(id : str):
  """  
  project fields:
  ```py
    _id : ObjectID
    projectName : str
    timeUpdated : str
    sessions : dict[url_id : str, filename : str]
    questions : array[str]
    _class : str
  ```
  """
  dbc.connect_db()
  project_filter = {'_id': ObjectId(id)}
  
  project = dbc.fetch_one(projectDB, project_filter)

  return project

def update_project_status(id : str, status : int):
  dbc.connect_db()
  dbc.update_doc(projectDB, {'_id': id}, {"projectStatus": status})


def get_user_project(username : str, project_index : int):
  """  
  project fields:
  ```py
    _id : ObjectID
    projectName : str
    timeUpdated : str
    sessions : dict[url_id : str, filename : str]
    questions : array[str]
    _class : str
  ```
  """
  dbc.connect_db()
  projects = get_user_project_ids(username)

  project_filter = {'_id': ObjectId(projects[project_index])}
  
  project = dbc.fetch_one(projectDB, project_filter)

  return project

def insert_findings(p_id, findings : dict):
  dbc.connect_db()
  return dbc.insert_one(findingDB, findings)

def insert_transcript(data : dict):
  dbc.connect_db()
  return dbc.insert_one(transcriptDB, data)
