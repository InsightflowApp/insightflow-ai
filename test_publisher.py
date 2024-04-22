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
    # {
    #     "_id":{
    #         "$oid":"6607464037ce70af1e36a4e1"
    #     },
    #     "projectName": "AI TEST gamma",
    #     "sessions": {
    #         "95d9a609-b252-48f9-a63f-3bdaaab21ab3":
    #           "template research interview 5.mp4",
    #         "24151495-6e4c-49e0-9516-0acb24b68464":
    #           "template research interview 1.mp4",
    #         "537fe7d8-6206-40d8-ab01-418674830656":
    #           "template research interview 4.mp4",
    #         "2a3bc8d6-014e-4863-8108-7cf39412cd43":
    #           "template research interview 3.mp4",
    #         "825361fb-d8bd-4bf8-bbbf-234e46a069fb":
    #           "template research interview 2.mp4"
    #     },
    #     "questions": [
    #         "[\"what are users' feedback on gamma templates?\"",
    #         ("\"What feedback do people provide regarding "
    #          "the current gamma templates?\""),
    #         ("\"What are people's expectations if they "
    #          "can upload their own templates to gamma?\"]"),
    #     ],
    #     "timeUpdated":"2024-03-27T20:42:06.821322119",
    #     "_class":"com.insightflow.insightflowbackend.pojo.Project",
    #     "projectStatus":{"$numberInt":"1"},
    #     "findingsId": "66197298f9c253c91749370a",
    #     "projectCreator": "65d72e205c187b23f3a793af"
    # }
]

for id in project_ids:
    channel.basic_publish(
        exchange="project.testing.exchange",
        routing_key="testing.project",
        body='{"projectId": "' + f"{id}" + '"}',
    )
