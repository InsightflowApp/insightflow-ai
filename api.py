from flask import Flask, request, send_file, send_from_directory
from flask_restx import Resource, Api, fields
import os
# import threading
# from time import sleep

import ai.mvp as mvp
import userdata.user_projects as up

app = Flask(__name__)
api = Api(app, title="InsightFlow AI API", version="0.3.0")

# easiest possible: analyze (questions, names_URLs)
an = api.namespace('analyze', description="all-in-one analysis from the database")
ans = api.namespace(
  'analyze-specific', 
  description="a more fine-tuned access to analysis, without having to insert data into the database"
)

ANALYSIS_DIR = os.getenv("ANALYSIS_DIR", "./demo")


password_model = api.model("Database Password", {
  'password': fields.String,
})


project_model = api.model('Project', {
  'database_password': fields.String,
  # names and urls should act like a mapping.
  'names': fields.List(fields.String),
  'urls': fields.List(fields.String),
  'questions': fields.List(fields.String),
})

analyses = dict()

session = api.model('Session', {
  '*': fields.Wildcard(fields.String)
})
response = api.model('Response', {'id': fields.String})

# thread_event = threading.Event()

# def backgroundTask():
#   while thread_event.is_set():
#     print('Background task running')
#     sleep(5)

analyses = dict()

def analyze(questions: list[str], audio_urls: dict[str,str], project_name: str):
  filename = f'{ANALYSIS_DIR}/{project_name}'

  analyses[project_name] = mvp.go(questions, audio_urls, filename)

@an.route('/<string:username>/<int:project_index>')
class Analysis(Resource):
  @an.expect(password_model)
  @an.marshal_with(response, code=200, description='Analysis started')
  def post(self, username : str, project_index : int):
    """Start analysis for a given project from the user. Password is for the database, not the specific user"""
    data : dict = an.payload

    password = data['password']
    if password != 'Insightflow666':
      return {'Access Denied': 'password is incorrect'}

    project : dict = up.get_user_project(username, project_index)

    if project is None:
      return {"Error": "project not found"}
    
    names = list()
    urls = list()
    for url, name in project["sessions"].items():
      names.append(name)
      urls.append(url)

    # names : list = project["sessions"].values()
    # urls : list = project["sessions"].keys()

    questions = project['questions']

    project_name = project['projectName']

    audio_urls = dict()
    for i in range(len(names)):
      extension = os.path.splitext(names[i])[1]
      audio_urls[names[i]] = f'https://insightflow-test.s3.us-east-2.amazonaws.com/{urls[i]}{extension}'

    # task = threading.Thread(target=mvp.go, args=[questions, audio_urls, project_name])
    # analyses[project_name] = task
    # task.start()

    # start task. It's not in the background but shouldn't take longer than 5 mins
    analyze(questions, audio_urls, project_name)

    return {'id': project_name}
    # return send_file(filename, download_name=f'{project_name}_results.md')

  def get(self, username, project_index):
    project = up.get_user_project(username, project_index)
    project_name = project["projectName"]

    filename = f"{ANALYSIS_DIR}/{project_name}/analysis/README.md"

    # if project_name not in analyses:
    #   return {'could not find': "either the server restarted or the analysis doesn't exist"}

    if os.path.exists(filename):
      return send_file(
        filename, 
        download_name=f'{project_name}_results.md'
      )

    return {'Not yet': 'response not ready'}



@ans.route('/<string:project_name>')
class AnalysisSpecific(Resource):
  @ans.expect(project_model)
  @ans.marshal_with(response, code=200, description='Analysis started')
  def post(self, project_name):
    data = an.payload

    password = data['password']
    if password != 'Insightflow666':
      return {'Access Denied': 'password is incorrect'}

    names = data['names']
    urls = data['urls']

    if len(names) != len(urls):
      return {'Error': 'urls and names need to be the same length'}
    questions = data['questions']

    audio_urls = dict()
    for i in range(len(names)):
      extension = os.path.splitext(names[i])[1]
      audio_urls[names[i]] = f'https://insightflow-test.s3.us-east-2.amazonaws.com/{urls[i]}{extension}'

    # task = threading.Thread(target=mvp.go, args=[questions, audio_urls, project_name])
    # analyses[project_name] = task
    # task.start()

    # start task. It's not in the background but shouldn't take longer than 5 mins
    analyze(questions, audio_urls, project_name)

    return {'id': project_name}
    # return send_file(filename, download_name=f'{project_name}_results.md')

  def get(self, project_name):
    filename = f"{ANALYSIS_DIR}/{project_name}/analysis/README.md"

    # if project_name not in analyses:
    #   return {'could not find': "either the server restarted or the analysis doesn't exist"}

    if os.path.exists(filename):
      return send_file(
        filename, 
        download_name=f'{project_name}_results.md'
      )

    return {'Not yet': 'response not ready'}


class Project(object):

  def __init__(self):
    self.questions = []
    self.transcripts = {}
    self.analyses = {}
  
  def add_question(self, question : str):
    self.questions.append(question)

  def add_transcript(self, name : str, data : str):
    self.transcripts[name] = data
  
  def analyze_transcripts(self):
    ...


if __name__ == '__main__':
  app.run(debug=True)

