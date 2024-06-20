import pika
import os
from dotenv import load_dotenv

load_dotenv()


"""
{"projectId": "6607464037ce70af1e36a4e1"}
"""


connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.environ["RABBITMQ_HOST"],
        port=os.environ["RABBITMQ_PORT"],
        credentials=pika.PlainCredentials(
            os.environ["RABBITMQ_USER"], os.environ["RABBITMQ_PASSWORD"]
        ),
    )
)

channel = connection.channel()

channel.exchange_declare(
    exchange="project.testing.exchange", exchange_type="direct", durable=True
)

project_ids = [
    "6607464037ce70af1e36a4e1",  # TEST 1 "AI TEST gamma"
    # 5 sessions: "template research interview" 1-5.mp4
    # 3 questions
    "666c9930f8d5192282d12d6e",  # TEST 2 improper project settings, should safely fail
]

for id in project_ids:
    channel.basic_publish(
        exchange="project.testing.exchange",
        routing_key="testing.project",
        body='{"projectId": "' + f"{id}" + '"}',
    )
