#!/usr/bin/env python3
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain

from langchain.prompts.chat import (
  ChatPromptTemplate,
  # SystemMessagePromptTemplate,
  # AIMessagePromptTemplate,
  # HumanMessagePromptTemplate
)
# from langchain.schema import AIMessage, HumanMessage, SystemMessage

from langchain.chat_models.base import BaseChatModel
from typing import List

import json
import os
from dotenv import load_dotenv

from ai.prompt_templates import map_template, reduce_template

'''
Minimum viable product

feeds all the transcripts to a conversational bot, asks the interview questions
'''
# TODO
# access Amazon S3 containers
# access MongoDB
# python server, automate testing + deployment (?)

# helpful pointers when prompting:
# name/role
# system instructions
# only pull from the call
# don't make the user prompt

MODEL='gpt-4-turbo-preview'
TOKEN_MAX=128_000

# sample list and files for demo purposes
question_list = [
  'What is the workflow for UX researchers/designers when analyzing user interviews?',
  'What are the pain points for UX researchers/designers when analyzing user interviews?',
  'How have UX researchers/designers tried to solve their pain points when analyzing user interviews?',
  'What are the pain points for UX researchers when presenting user research results to other stakeholders?',
  'What are the opinions of UX researchers/designers regarding the use of AI in user research?',
]

sample_files = [
  "simple_transcripts/interview-video-1.txt",
  "simple_transcripts/interview-video-2.txt",
]

load_dotenv()

def quick_test(llm_model: str = MODEL, country : str = "Australia"):
  '''quick test to make sure model is working.'''
  prompt = ChatPromptTemplate.from_template("Hi, there! What's the capital of {country}?")
  model = ChatOpenAI(model=llm_model)
  output_parser = StrOutputParser()

  chain = {'country': RunnablePassthrough()} | prompt | model | output_parser

  print(chain.invoke(country))
  return chain


def simple_transcript(filename : str, dest_name : str | None = None) -> bool:
  '''create a simple transcript from an existing complex one.'''
  transcript = {}
  with open(filename, 'r') as f:
    transcript = json.loads(f.read())
  
  if dest_name is None:
    dest_name = f'simple_transcripts/{os.path.splitext(os.path.split(filename)[1])[0]}.txt'

  with open(dest_name, 'w') as f:
    print(transcript['results']['channels'][0]['alternatives'][0]['paragraphs']['transcript'], file=f)

  return True

# in the future: back up with prompt questions generated by examples and 
                       # another chat model call

def make_chain(llm : BaseChatModel, template : str, input_variables = ['docs'], partial_variables : dict[str, list[str]] = {}) -> LLMChain:
  prompt = PromptTemplate(
    template=template,
    input_variables=['docs'],
    partial_variables=partial_variables
  )

  chain = (
    {'docs': RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
  )
  return chain


from os.path import split as split_path, splitext

def mvp(question_list : list[str] = question_list, files : list[str] = sample_files):
  response_dir = "mvp_response"
  # gather transcript
  questions : str = '\n'.join([f'{i+1}. {question_list[i]}' for i in range(len(question_list))])

  # load documents
  docs : List[Document] = []
  for filename in files:
    loader = TextLoader(filename)
    docs += loader.load()

  llm = ChatOpenAI(model=MODEL, temperature=0)
  partial_var = {'questions': questions}

  # Map
  map_chain = make_chain(llm, map_template, partial_variables=partial_var)
  map_responses = map_chain.batch(docs)
  # print responses to files
  for i in range(len(files)):
    filename = splitext(split_path(files[i])[1])[0]
    output_file = f'{response_dir}/{filename}_response.txt'
    with open(output_file, 'w') as out:
      print(map_responses[i], file=out)

  print("Received all responses. Calling reduce.")

  # Reduce
  map_response = '\n\n'.join(map_chain.batch(docs))
  reduce_chain = make_chain(llm, reduce_template, partial_variables=partial_var)

  reduce_response = reduce_chain.invoke(map_response)

  with open(f'{response_dir}/all_responses.txt', 'w') as file:
    print(reduce_response, file=file)

  print("done.")

  return True
  