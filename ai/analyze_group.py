from langchain_community.document_loaders import JSONLoader
import json
from pathlib import Path
from pprint import pprint

QUESTIONS = 'questions'
DOCS = 'documents'

def metadata_func(record : dict, metadata : dict) -> dict:
  '''for document loading. see GroupList.create()'''
  metadata['speaker'] = record.get('speaker')
  metadata['start'] = record.get('start')
  metadata['end'] = record.get('end')

  return metadata

class GroupList(object):
  '''create, read, update, or delete a group of files to analyze.'''

  '''
  a mapping of transcripts from their sample places to a folder 
  containing all of them in their simplified form
  '''

  def __init__(self, name : str = 'default', question_lst : list = []) -> None:
    self.filedir = f'./group_{name}'
    self.data = {
      QUESTIONS: question_lst,
      DOCS: {},
    }
    self.id = 0

  def create(self, file_path : str) -> bool:
    '''add relevant json to a file being tracked here'''

    loader = JSONLoader(
      file_path=file_path,
      jq_schema='''.results.channels[0].alternatives[0].paragraphs.paragraphs[] | {"text": [.sentences[].text] | join(" ")} + {speaker, start, end}''',
      content_key='text',
      metadata_func=metadata_func
    )

    self.data[DOCS][file_path] = loader.load()

    self.id += 1
    return True

  def read(self, file_path : str):
    '''read the transcript info from the modified json entry'''
    pprint(self.data[DOCS][file_path])
    return self.data[DOCS][file_path]

  def update(self, file_path : str):
    '''reimport a file's transcript'''

    loader = JSONLoader(
      file_path=file_path,
      jq_schema='''.results.channels[0].alternatives[0].paragraphs.paragraphs[] | {"text": [.sentences[].text] | join(" ")} + {speaker, start, end}''',
      content_key='text',
      metadata_func=metadata_func
    )

    self.data[DOCS][file_path] = loader.load()

    return True

  def delete(self, file_path : str):
    pass

  def add_question(self, question : str):
    '''manually add questions to ask for relevant info'''
    self.data[QUESTIONS].append(question)
    return True

  def generate_questions(self, sample_question : str):
    '''generate questions to retrieve relevant information from the docs'''
    # not implemented
    pass

  def analyze(self):
    '''analyze the documents based on the questions'''
    

    pass

