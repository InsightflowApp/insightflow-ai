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
    exchange="project.analysing.exchange", exchange_type="direct", durable=True
)

channel.basic_publish(
    exchange="project.analysing.exchange",
    routing_key="analysing.project",
    body='{"projectId": "6607464037ce70af1e36a4e1"}',
)
