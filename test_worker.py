from dotenv import load_dotenv
import pika
import os
from worker import callback


def main():

    load_dotenv()

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

    channel.queue_declare(queue="project.testing.queue", durable=True)
    print(" [*] Waiting for messages. To exit press CTRL+C")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="project.testing.queue", on_message_callback=callback)

    channel.start_consuming()


if __name__ == "__main__":
    main()
