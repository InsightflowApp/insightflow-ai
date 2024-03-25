#!/usr/bin/env python
from sys import stderr
import sys
import pika
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import traceback

from transcribe import transcribe_async as trs

from pika.adapters.blocking_connection import BlockingChannel

from ai import mvp
from ai.json_response import md_to_json

from db import user_projects as up
from db import db_connect as dbc

from bson.objectid import ObjectId

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
      ),
      heartbeat=600,
      blocked_connection_timeout=300
    )
  )

  channel = connection.channel()

  channel.queue_declare(queue='project.analysing.queue', durable=True)
  print(' [*] Waiting for messages. To exit press CTRL+C')

  channel.basic_qos(prefetch_count=1)
  channel.basic_consume(queue='project.analysing.queue', on_message_callback=callback)

  channel.start_consuming()


def callback(ch : BlockingChannel, method, properties, body : bytes):
  """
  this is called whenever a message is retrieved from the mQueue
  """
  print(f" [x] Received {body.decode()}")
  incoming = json.loads(body)

  project_id = incoming["projectId"]

  try:
    project = up.get_project_by_id(project_id)
  except Exception as e:
    print(f"could not connect to db: {e}", file=stderr)
    return

  # if "projectStatus" in project and project["projectStatus"] == 2:
  #   message = json.dumps({
  #       "projectId": project_id,
  #       "code": 1, # 0 for fail, 1 for success
  #     })

  # else:
  try:
    question_list = project["questions"]
    sessions = project["sessions"]

    # change projectStatus to 1
    up.update_project_status(project_id, 1)

    transcripts = transcribe_project(sessions)

    simple_transcripts = list()
    # 
    for url_str, name in sessions.items():
      transcripts[name]["video_id"] = url_str
      transcripts[name]["title"] = name
      transcript_id = up.insert_transcript(transcripts[name])

      simple_transcripts.append(
        f"Transcript id: {transcript_id}\n\n" +
        transcripts[name]["captions"]
      )

    # analyze  
    result = mvp.map_reduce(question_list, simple_transcripts)


    # store findings in Findings collection
    # TODO more db stuff
    findings = construct_findings(project_id, result)
    findingsId = up.insert_findings(findings)
  
    # update projectStatus to 2
    up.update_project_status(project_id, 2, findingsId)

    message = json.dumps({
      "projectId": project_id,
      "code": 1, # 0 for fail, 1 for success
    })

  except:
    # except: set project status to -1, send code 0
    up.update_project_status(project_id, -1)

    message = json.dumps({
      "projectId": project_id,
      "code": 0, # 0 for fail, 1 for success
    })

    traceback.print_exc(file=stderr)
  # end else

  try:
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

  except Exception as e:
    print(f"Publish error: {e}", file=stderr)


def transcribe_project(sessions: dict) -> dict:
  """
  returns transcripts for videos in project
  
  example response fields, truncated:
  ```
  {
    "video1.mp4": {
      "metadata" : dict
      "results": {
        "channels": list
        "utterances": [
          "start": 0.08
          "end": 7.705
          "confidence": 0.9782485
          "channel": 0
          "transcript": "Hi. Thank you for calling Premier Phone Services. This call may be recorded for quality and training purposes. My name is Tom, and I'll be assisting you. How are you today?"
          "words": list[dict]
          "speaker": 0
          "id": uuid  # unrelated
        ]
      }
    },
    "video2.mp4": ...
  }
  ```
  """

  def format_pair(name: str, url_str: str):
    extension = os.path.splitext(name)[1]
    url = f'https://insightflow-test.s3.us-east-2.amazonaws.com/{url_str}{extension}'
    return (name, url)

  audio_urls = {name: url for name, url in map(
    format_pair, 
    sessions.values(), 
    sessions.keys())}
  
  return trs.transcribe_urls(audio_urls)


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

  response = md_to_json(markdown_content)

  response["projectId"] = id

  return response


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)