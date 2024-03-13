#!/usr/bin/env python
import pika
import time
import json
import os
from dotenv import load_dotenv

from pika.adapters.blocking_connection import BlockingChannel

from ai import mvp
from db import user_projects as up
"""
Receive logs from InsightFlow queue and process them
"""

load_dotenv()

ANALYSIS_DIR = os.getenv("ANALYSIS_DIR", "./demo")

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

analyses = dict()

def analyze_project(id : str):
  project = up.get_project_by_id(id)

  project_name = project['projectName']
  filename = f'{ANALYSIS_DIR}/{project_name}'

  names = list()
  urls = list()
  for url, name in project["sessions"].items():
    names.append(name)
    urls.append(url)

  audio_urls = dict()
  for i in range(len(names)):
    extension = os.path.splitext(names[i])[1]
    audio_urls[names[i]] = f'https://insightflow-test.s3.us-east-2.amazonaws.com/{urls[i]}{extension}'

  analyses[project_name] = mvp.go(
    project["questions"],
    audio_urls,
    filename,
  )


def callback(ch : BlockingChannel, method, properties, body : bytes):
  print(f" [x] Received {body.decode()}")
  message = json.loads(body)

  project_id = message["projectId"]

  # change projectStatus to 1
  # TODO mongodb stuff
  up.update_project_status(project_id, 1)

  # analyze  
  # try: analyze
  analyze_project(project_id)
  # except: set project status to -1, send code 0

  # store findings in Findings collection
  # TODO more db stuff


  # update projectStatus to 2
  up.update_project_status(project_id, 2)

  # send confirmation message to confirm.analyzing
  message = json.dumps({
    "projectId": project_id,
    "code": 1, # 0 for fail, 1 for success
  })

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


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='project.analysing.queue', on_message_callback=callback)

channel.start_consuming()


