from flask import Flask
from flask_restx import Resource, Api, fields
import os
import json

from ai.transcribe_video import transcribe
from ai.mvp import mvp

app = Flask(__name__)
api = Api(app, title="InsightFlow AI API", version="0.2.0")

ts = api.namespace('transcribe', description="Transcription operations")
sa = api.namespace('single_analysis', description="Analysis of one transcript. Not functional yet.")
ga = api.namespace('group_analysis', description="Analysis of a group. Not functional yet.")
sample = api.namespace('sample_list', description="Sample .mp3s, .jsons, and .txts used for testing")

SAMPLE_AUDIO_DIR = 'sample_audio'
SAMPLE_TRANSCRIPT_DIR = 'sample_transcripts'

transcript_model = api.model('Transcript', {
  'source': fields.String,
})

analysis = ""
group = []

def transcript_info(content):
  return {
    'Content': content["results"]["channels"][0]["alternatives"][0]["transcript"],
    # 'Topics': content["results"]["topics"]
  }

@ts.route('/<string:filename>')
class Transcription(Resource):
  def get(self, filename):
    '''retrieve an existing sample transcript'''
    if filename not in os.listdir(path=SAMPLE_TRANSCRIPT_DIR):
      return {"Error": "File not found. Check sample_transcripts"}
 
    content = {}
    with open(f'{SAMPLE_TRANSCRIPT_DIR}/{filename}', 'r') as file:
      content = json.load(file)
    return transcript_info(content)


  def post(self, filename):
    '''create a new transcript from a sample audio file'''
    if filename not in os.listdir(path=SAMPLE_AUDIO_DIR):
      return {"Error": "File not found. Check sample_audio"}
    
    dest_pathname = f'{SAMPLE_TRANSCRIPT_DIR}/{os.path.splitext(filename)[0]}.json'
    dest = transcribe(f'{SAMPLE_AUDIO_DIR}/{filename}', dest_pathname)
    return {"Transcript": dest}


@sa.route('/<string:filename>')
@sa.response(404, 'Transcript not found')
@sa.param('filename', 'The transcript to analyze')
class SingleAnalysis(Resource):
  def get(self):
    return {'response': 'not implemented yet.'}

@ga.route('/analyze')
class GroupAnalysis(Resource):
  '''Analyze a group of files'''
  # post: add files to group, if they exist
  # get: get analysis of current group
  # delete: remove from group, "all" for all
  pass

@ga.route('/')
class GroupList(Resource):
  '''modify the group to analyze'''
  # post: add files to group, if they exist
  @ga.expect(transcript_model)
  def post(self):
    '''Add a transcript to the list to analyze.'''
    tsc = api.payload
    if tsc['source'] not in os.listdir(path=SAMPLE_TRANSCRIPT_DIR):
      return {"Error": "File not found."}
    for t in group:
      if tsc['source'] == t['source']:
        return t
    group.append(tsc)
    return tsc

    
  def get(self):
    '''see the active list of transcripts to analyze'''
    return group
  # delete: remove from group, "all" for all
  # def delete(self):
  #   pass

@sample.route('/audio')
class AudioFiles(Resource):
  def get(self):
    """
    Returns a list of sample audio file names.
    """
    filenames = os.listdir(path=SAMPLE_AUDIO_DIR)
    return {"files": filenames}

@sample.route('/transcript_jsons')
class TranscriptJSONs(Resource):
  def get(self):
    """
    Returns a list of sample transcript file names.
    """
    filenames = os.listdir(path=SAMPLE_TRANSCRIPT_DIR)
    return {"files": filenames}

if __name__ == '__main__':
  app.run(debug=True)

