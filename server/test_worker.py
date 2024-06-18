from dotenv import load_dotenv
import pika
import os
import sys
from worker import callback
from server.logger import logger

LAST_STATUS=4

def main():

    if "--clear-logs" in sys.argv:
        print("cleared logs.")
        logger.clear()

    load_dotenv()
    os.environ["CHAN_NAME"] = "project.testing"
    chan_name = "project.testing"

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


if __name__ == "__main__":
    main()
