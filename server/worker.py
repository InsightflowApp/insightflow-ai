#!/usr/bin/env python
import sys
import pika
import json
import os
from dotenv import load_dotenv

from pika.adapters.blocking_connection import BlockingChannel

from db import user_projects as up

from server.update_project import (
    transcribe_project,
    analyze_individual_tscs,
    group_questions,
    format_response,
)

from server.logger import logger

"""
Receive logs from InsightFlow queue and process them.

This is the main file. It handles RabbitMQ interactions, and 
performs actions on the project based on its phase.

For more information about each action, see update_project.py.
"""

# TODO modularity in progress
# NEXT with modulation:
# - testing suite, patch in fake API responses

LAST_STATUS = 4

# "projectStatus"
# For projectStatus i, enact step i+1 until final status (LAST_STATUS) is reached.
project_status_table = {
    0: transcribe_project,  # not started
    1: analyze_individual_tscs,  # transcripts done
    2: group_questions,  # individual analysis done
    3: format_response,  # grouping questions done
    # 4, JSON formatting done
}


def main():
    """
    Connects to RabbitMQ. Uses the callback function to handle messages.
    Messages are currently bytes which can be loaded as strings to JSON:
    {"projectId": "abcdef1234567890" }
    """

    # TODO make args to handle log clearing
    # if clear-logs, call logger.clear()

    if "--clear-logs" in sys.argv:
        logger.info("cleared logs.")
        logger.clear()

    load_dotenv()
    chan_name = os.getenv("CHAN_NAME")

    logger.info(
        f"host: {os.environ['RABBITMQ_HOST']}\nport: {os.environ['RABBITMQ_PORT']}"
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ["RABBITMQ_HOST"],
            port=os.environ["RABBITMQ_PORT"],
            credentials=pika.PlainCredentials(
                os.environ["RABBITMQ_USER"], os.environ["RABBITMQ_PASSWORD"]
            ),
            heartbeat=600,
            blocked_connection_timeout=300,
        )
    )

    channel = connection.channel()

    # for sending messages to self
    channel.exchange_declare(
        exchange=f"{chan_name}.exchange", exchange_type="direct", durable=True
    )

    channel.queue_declare(queue=f"{chan_name}.queue", durable=True)
    print(" [*] Waiting for messages. To exit press CTRL+C")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=f"{chan_name}.queue", on_message_callback=callback)

    channel.start_consuming()


def callback(ch: BlockingChannel, method, properties, body: bytes):
    """
    this is called whenever a message is retrieved from the mQueue.
    The function updates a project and completes a step as defined above.
    """
    logger.debug(f"entered callback", f"{body.decode()[:500]=}", sep="\n")
    logger.info(f"Received message from queue")

    incoming = json.loads(body)
    project_id = incoming["projectId"]

    chan_name = os.getenv("CHAN_NAME")
    logger.info(f"callback: {chan_name=}")

    try:
        logger.info(f"grabbing project {project_id}")

        project = up.get_project_by_id(project_id)
    except Exception as e:
        logger.error(f"callback: could not connect to db: {e}")
        return

    status = incoming.get("projectStatus", 0)
    status = max(status, 0)
    logger.debug(f"project status is {status}")

    # send message
    try:
        # this is where the magic happens
        new_status, outgoing = project_status_table[status](project, incoming)
    except Exception as e:
        logger.error(
            f"callback: exception with project {project_id}, status {status}",
            exception=e,
        )
        # except: set project status to -1, send code 0
        if status < 1:
            new_status, outgoing = -1, {}
            logger.info("callback: updating project status to -1.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            up.update_project_status(project_id, new_status)
        else:
            logger.info("callback: keeping status the same")
            ch.basic_nack(delivery_tag=method.delivery_tag)
        logger.debug("callback: Exception done")
        return

    logger.info(f"{new_status=}")
    if new_status < LAST_STATUS:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        send_response(ch, project_id, new_status, outgoing)

    elif new_status == LAST_STATUS:
        message = json.dumps(
            {
                "projectId": project_id,
                "code": 1,  # 0 for fail, 1 for success
            }
        )

        try:
            logger.debug("sending confirmation message")
            # send confirmation message to confirm.analyzing
            ch.basic_publish(
                exchange=f"{chan_name}.exchange",
                routing_key=f"confirm.{chan_name.split('.')[1]}",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                ),
            )

            # done!
            logger.info(f"Done with project {project_id}. New status: {new_status}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"callback: confirmation message error", exception=e)

    logger.debug("exiting callback")


def send_response(ch: BlockingChannel, project_id, project_status, content):
    """send back to analyzing queue"""
    data = dict()
    data["projectId"] = project_id
    data["projectStatus"] = project_status
    data.update(content)
    chan_name = os.getenv("CHAN_NAME")

    ch.basic_publish(
        exchange=f"{chan_name}.exchange",
        routing_key=f"{chan_name.split('.')[1]}.project",
        body=json.dumps(data),
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
