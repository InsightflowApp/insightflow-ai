#!/usr/bin/env python
from sys import stderr
import sys
import pika
import json
import os
from dotenv import load_dotenv
import traceback

from transcribe import transcribe_async as trs

from pika.adapters.blocking_connection import BlockingChannel

from ai import mvp
from ai.json_response import md_to_json

from db import user_projects as up

"""
Receive logs from InsightFlow queue and process them.

This is the main file.
"""

# TODO modularity in progress
# CURRENT STATE:
#
# - transcription phase
# - analysis phase
# - runs one, then sends a message in the queue to continue
#   to the next step
# - testable with test_worker and test_publisher
#
# NEXT with modulation:
# - move callback contents into its own file
#   (basically everything below send_response)
# - testing suite, patch in fake API responses
# - more phases (split analysis into 3)
# analysing or testing


def step_1(p, i):
    """step 1: transcribe"""
    print("in step 1")
    response = transcribe_project(p, i)
    print("finished step 1")
    return response


def step_2(p, i):
    """step 2: analyze individual transcripts"""
    print("in step 2")
    response = analyze_individual_tscs(p, i)
    print("finished step 2")
    return response


def step_3(p, i):
    """step 3: group analysis questions"""
    print("in step 3??")
    return group_questions(p, i)


def step_4(p, i):
    """step 4: format response to JSON"""
    return format_response(p, i)


# TODO move to own file, update_project
# "projectStatus"
next_table = {
    0: step_1,  # not started
    1: step_2,  # transcripts done
    # 2: step_3,  # individual analysis done
    # 3: step_4,  # grouping questions done
    # 4: ...,  # JSON formatting done
    # 5: ...,  # done
}


def main():
    """
    Connects to RabbitMQ. Uses the callback function to handle messages.
    Messages are currently bytes which can be loaded as strings to JSON:
    {"projectId": "abcdef1234567890" }
    """

    load_dotenv()
    chan_name = os.getenv("CHAN_NAME")

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
    print(f" [x] Received {body.decode()[:300]}")
    incoming = json.loads(body)
    project_id = incoming["projectId"]

    chan_name = os.getenv("CHAN_NAME")
    print(f"callback: {chan_name=}")

    try:
        print(f"grabbing project {project_id}")
        project = up.get_project_by_id(project_id)
    except Exception as e:
        print(f"could not connect to db: {e}", file=stderr)
        return

    status = incoming.get("projectStatus", 0)
    print(f"project status is {status}")

    # send message
    try:
        # this is where the magic happens
        new_status, outgoing = next_table[status](project, incoming)
    except Exception as e:
        # except: set project status to -1, send code 0
        up.update_project_status(project_id, -1)
        message = json.dumps(
            {
                "projectId": project_id,
                "code": 0,  # 0 for fail, 1 for success
                "message": f"{e}",
            }
        )
        send_response(ch, project_id, -1, message)
        traceback.print_exc(file=stderr)

    print(f"{new_status}")
    if new_status < 2:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        send_response(ch, project_id, new_status, outgoing)

    elif new_status == 2:
        message = json.dumps(
            {
                "projectId": project_id,
                "code": 1,  # 0 for fail, 1 for success
            }
        )

        try:
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
            print(" [x] Done")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Publish error: {e}", file=stderr)


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


def transcribe_project(project, incoming={}) -> tuple[int, dict]:
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
            "start": 0.08,
            "end": 7.705,
            "confidence": 0.9782485,
            "channel": 0,
            "transcript": "Recording now. Let's begin...",
            "words": list[dict],
            "speaker": 0,
            "id": uuid,  # unrelated
          ]
        }
      },
      "video2.mp4": ...
    }
    ```
    """

    def format_pair(name: str, url_str: str):
        extension = os.path.splitext(name)[1]
        url = f"{os.getenv('INSIGHTFLOW_S3')}/{url_str}{extension}"
        return (name, url)

    sessions = project["sessions"]
    audio_urls = {
        name: url for name, url in map(format_pair, sessions.values(), sessions.keys())
    }

    # run API call and format
    transcripts = trs.transcribe_urls(audio_urls)
    simple_transcripts = list()
    # relate transcript IDs and video IDs
    tscid_vidid = dict()
    # store transcripts in DB
    for url_str, name in sessions.items():
        transcripts[name]["video_id"] = url_str
        transcripts[name]["title"] = name
        transcript_id = up.insert_transcript(transcripts[name])

        tscid_vidid[transcript_id] = url_str

        simple_transcripts.append(
            f"Transcript id: {transcript_id}\n\n" + transcripts[name]["captions"]
        )

    up.update_project_status(str(project["_id"]), 1)
    return 1, {"simple_transcripts": simple_transcripts, "tscid_vidid": tscid_vidid}


def analyze_individual_tscs(project, incoming) -> tuple[int, dict]:
    # right now, this does the entirety of steps 2-4
    # analyze
    question_list = project["questions"]
    project_id = incoming["projectId"]
    simple_transcripts = incoming["simple_transcripts"]
    tscid_vidid = incoming["tscid_vidid"]
    outgoing = mvp.map_reduce(question_list, simple_transcripts)

    # store findings in Findings collection
    findings = construct_findings(project_id, outgoing, tscid_vidid)
    findingsId = up.insert_findings(findings)

    up.update_project_status(str(project["_id"]), 2)
    return 2, {"individual_responses": outgoing}


def group_questions(project, incoming) -> tuple[int, dict]:

    outgoing = ...
    return 3, {"grouped_responses": outgoing}


def format_response(project, incoming) -> tuple[int, dict]:

    outgoing = ...
    return 4, {"formatted_response": outgoing}


def timestamp_to_seconds(timestamp_str: str) -> float:
    hms = timestamp_str.split(sep=":")
    return 3600 * int(hms[0]) + 60 * int(hms[1]) + float(hms[2])


def construct_findings(id, markdown_content: str, transcript_video_dict) -> dict:
    response = md_to_json(markdown_content)

    response["projectId"] = id
    vid_count = len(transcript_video_dict)

    # print(f'{transcript_video_dict=}')  # TODO delete

    count = 5
    while (len(response["questions"]) == 0) and (count > 0):
        print(f"empty questions: {id}", file=stderr)
        response = md_to_json(markdown_content)
        count -= 1

    if len(response["questions"]) == 0:
        # TODO generate backup questions here
        raise AttributeError("could not convert questions to json")

    # add corresponding video_id for each transcript
    for question in response["questions"]:
        for theme in question["themes"]:
            count_tracker = set()
            # theme["count"] = len(theme["quotes"])
            theme["total"] = vid_count
            for quote in theme["quotes"]:
                tsc_id = quote.get("transcript_id", None)
                vid_id = transcript_video_dict.get(tsc_id, None)
                count_tracker.add(tsc_id)
                if vid_id is not None:
                    quote["video_id"] = vid_id
                else:
                    print(
                        "could not find "
                        + ("transcript" if tsc_id is None else "video")
                        + f'id for quote "{quote.get("quote", "")}"',
                        file=stderr,
                    )

                # reformat timestamps
                start = timestamp_to_seconds(quote.get("timestamp_start", "00:00:00.0"))
                end = timestamp_to_seconds(quote.get("timestamp_end", "00:00:00.0"))
                quote["timestamp_start"] = start
                quote["timestamp_end"] = end

            theme["count"] = len(count_tracker)

    return response


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
