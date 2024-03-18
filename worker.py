#!/usr/bin/env python
from sys import stderr
import pika
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from transcribe import transcribe_async as trs

from pika.adapters.blocking_connection import BlockingChannel

from ai import mvp
from db import user_projects as up
from db import db_connect as dbc

"""
Receive logs from InsightFlow queue and process them
"""

def main():

  load_dotenv()

  connection = pika.BlockingConnection(
    pika.ConnectionParameters(
      host=os.environ["RABBITMQ_HOST"],
      port=os.environ["RABBITMQ_PORT"],
      credentials=pika.PlainCredentials(
        os.environ["RABBITMQ_USER"], 
        os.environ["RABBITMQ_PASSWORD"]
      )
    )
  )

  channel = connection.channel()

  channel.queue_declare(queue='project.analysing.queue', durable=True)
  print(' [*] Waiting for messages. To exit press CTRL+C')

  channel.basic_qos(prefetch_count=1)
  channel.basic_consume(queue='project.analysing.queue', on_message_callback=callback)

  channel.start_consuming()


def analyze_transcripts(question_list: list[str], transcripts: dict):
  print("made it to analyze_transcripts")
  print(f"{transcripts=}")

  transcripts_simple = list()

  # add transcripts to DB
  for name, content in transcripts.items():
    alternatives = (
      content['results']['channels'][0]
      ['alternatives'][0]
    )

    if "paragraphs" in alternatives and 'transcript' in alternatives['paragraphs']:
    # get simple version of transcripts
      transcripts_simple.append(
        f"{name}\n\n"
        f"{alternatives['paragraphs']['transcript']}"
      )

  print(f"{transcripts_simple=}")

  result = mvp.map_reduce(
    question_list,
    transcripts_simple
  )

  return result


def transcribe_project(sessions: dict) -> dict:
  """returns transcripts for videos in project"""

  def format_pair(name: str, url_str: str):
    extension = os.path.splitext(name)[1]
    url = f'https://insightflow-test.s3.us-east-2.amazonaws.com/{url_str}{extension}'
    return (name, url)

  audio_urls = {name: url for name, url in map(
    format_pair, 
    sessions.values(), 
    sessions.keys())}
  
  return trs.transcribe_urls(audio_urls)


def callback(ch : BlockingChannel, method, properties, body : bytes):
  print(f" [x] Received {body.decode()}")
  message = json.loads(body)

  project_id = message["projectId"]


  try:
    project = up.get_project_by_id(project_id)

    question_list = project["questions"]
    sessions = project["sessions"]

    # change projectStatus to 1
    up.update_project_status(project_id, 1)


    transcripts = transcribe_project(sessions)

    # 
    for url_str, name in sessions.items():
      transcripts[name]["video_id"] = url_str
      transcripts[name]["title"] = name
      up.insert_transcript(transcripts[name])

    # analyze  
    # try: analyze
    result = analyze_transcripts(question_list, transcripts)
    # except: set project status to -1, send code 0

    # store findings in Findings collection
    # TODO more db stuff
    findings = construct_findings(project_id, result)
    findingsId = up.insert_findings(project_id, findings)
  
    # update projectStatus to 2
    up.update_project_status(project_id, 2, findingsId)

    message = json.dumps({
      "projectId": project_id,
      "code": 1, # 0 for fail, 1 for success
    })

  except Exception as e:
    up.update_project_status(project_id, -1)
    
    message = json.dumps({
      "projectId": project_id,
      "code": 0, # 0 for fail, 1 for success
    })
    print(f"Error: {e}", file=stderr)

    # send confirmation message to confirm.analyzing
  ch.basic_publish(
    exchange='project.analysing.exchange',
    routing_key='confirm.analysing',
    body=message,
    properties=pika.BasicProperties(
        delivery_mode=pika.DeliveryMode.Persistent
    )
  )

  # done!
  print(" [x] Done")
  ch.basic_ack(delivery_tag=method.delivery_tag)



"""
 [*] Waiting for messages. To exit press CTRL+C
 [x] Received {"projectId":"65ed715a7abe2b3a1f58cc55"}
 [x] Done
 [x] Received {"projectId":"65ed71677abe2b3a1f58cc56"}
 [x] Done
 [x] Received {"projectId":"65ed73707abe2b3a1f58cc57"}
 [x] Done
"""

def construct_findings(id, markdown_content : str) -> dict:
  # {
  # "Id": "auto generated id",
  # "questions": [
  #       {
  #         "questionTitle": "string",
  #         "questionAnalysis": "string",
  #         "topics": [
  #           {
  #             "quote": [
  #               {
  #                 "quoteParticipant": "string",
  #                 "quoteTimeStamp": "string",
  #                 "quoteText": "string",
  #                 "sessionID": "string"
  #               }
  #             ],
  #             "topicName": "string",
  #             "numOfAgreedParticipants": 0,
  #             "totalParticipants": 0
  #           }
  #         ]
  #       }
  #     ],
  # "markdownContent": "findings markdown string"
  # }

  response = dict()

  response["findingId"] = id
  response["markdownContent"] = markdown_content

  return response


if __name__ == "__main__":
  main()
