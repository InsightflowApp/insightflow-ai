from flask import Flask, request
from flask_restx import Resource, Api, fields
import os
import threading
from time import sleep

import ai.mvp as mvp

app = Flask(__name__)
api = Api(app, title="InsightFlow AI API", version="0.3.0")

# easiest possible: analyze (questions, names_URLs)
an = api.namespace('analyze', description="all-in-one analysis, without username stuff")

project_model = api.model('Project', {
  'password': fields.String,
  # names and urls should act like a mapping.
  'names': fields.List(fields.String),
  'urls': fields.List(fields.String),
  'questions': fields.List(fields.String),
})

# How it looks:
# POST:
# {
#   "password": "Insightflow666",
#   "names": [
#     "template research interview 3.mp4", "template research interview 2.mp4", "template research interview 4.mp4", "template research interview 5.mp4"
#   ],
#   "urls": [
#     "4e72f777-d179-452e-8629-8ef4d76f54ad", "cb9f1ff5-178f-4c46-977d-0940fc8a9b13", "9e26f983-d3fc-438f-988d-c1c2a93bf755", "44b8d19b-531a-4947-b075-05315a2ade90"
#   ],
#   "questions": [
#     "How do our users define the term \"templates\"?", "What feedback do people provide regarding the current gamma templates?", "What are people's expectations if they can upload their own templates to gamma?"
#   ]
# }

analyses = dict()

session = api.model('Session', {
  '*': fields.Wildcard(fields.String)
})

response = api.model('Response', {'id': fields.String})

thread_event = threading.Event()

def backgroundTask():
  while thread_event.is_set():
    print('Background task running')
    sleep(5)

@an.route('/<string:project_name>')
class Analysis(Resource):
  @an.expect(project_model)
  @an.marshal_with(response, code=200, description='Analysis started')
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

    task = threading.Thread(target=mvp.go, args=[questions, audio_urls, project_name])
    analyses[project_name] = task
    task.start()

    return {'id': project_name}

  def get(self, project_name):
    filename = f'{project_name}/analysis/README.md'

    if os.path.exists(filename):
      with open(filename, 'r') as file:
        response = file.read()
      return {'response': response}, 200

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

