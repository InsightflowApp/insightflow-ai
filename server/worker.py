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

from server.logger import logger

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
    logger.debug("in step 1")
    response = transcribe_project(p, i)
    logger.debug("finished step 1")
    return response


def step_2(p, i):
    """step 2: analyze individual transcripts"""
    logger.debug("in step 2")
    response = analyze_individual_tscs(p, i)
    logger.debug("finished step 2")
    return response


def step_3(p, i):
    """step 3: group analysis questions"""
    logger.debug("in step 3??")
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
        new_status, outgoing = next_table[status](project, incoming)
    except Exception as e:
        logger.error(f"callback: exception with project {project_id}, status {status}", exception=e)
        new_status, outgoing = -1, {}
        logger.info("callback: updating project status to -1.")
        # except: set project status to -1, send code 0
        up.update_project_status(project_id, -1)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.debug("callback: Exception done")
        return

    logger.info(f"{new_status=}")
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
            logger.info(f"Done with project {project_id}. New status: {status}")
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
    logger.debug("entered transcribe_project", f"project keys: {project.keys()}", f"sessions type: {type(project['sessions'])}", sep="\n\t")
    if type(project["sessions"]) == dict:
        logger.info("TRANSCRIBE: these sessions are a dict: assuming old format.")

        def format_pair(name: str, url_str: str):
            extension = os.path.splitext(name)[1]
            url = f"{os.getenv('INSIGHTFLOW_S3')}/{url_str}{extension}"
            return (name, url)

        sessions = list()
        for k, v in project["sessions"].items():
            sessions.append(
                {
                    "video_id": k,
                    "video_name": v,
                }
            )

        audio_urls = {
            name: url
            for name, url in map(
                format_pair, project["sessions"].values(), project["sessions"].keys()
            )
        }

    else:
        logger.info("TRANSCRIBE: these sessions are a list: assuming new format.")

        def make_audio_url(session: dict):
            extension = os.path.splitext(session["video_name"])[1]
            url = f"{os.getenv('INSIGHTFLOW_S3')}/{session['video_id']}{extension}"
            return (session["video_name"], url)

        sessions = project["sessions"]

        # session: video_name, video_id, transcript_id
        audio_urls = {name: url for name, url in map(make_audio_url, sessions)}

    # run API call and format
    logger.debug("calling transcribe_urls")
    transcripts = trs.transcribe_urls(audio_urls)
    logger.debug("out of transcribe_urls")
    simple_transcripts = list()
    # relate transcript IDs and video IDs
    tscid_vidid = dict()
    # store transcripts in DB
    for s in sessions:
        name = s["video_name"]
        vid_id = s["video_id"]

        transcripts[name]["video_id"] = vid_id
        transcripts[name]["title"] = name
        transcript_id = up.insert_transcript(transcripts[name])

        s["transcript_id"] = transcript_id
        tscid_vidid[transcript_id] = vid_id

        simple_transcripts.append(
            f"Transcript id: {transcript_id}\n\n{transcripts[name]['paragraphs']['transcript']}"
        )

    if type(project["sessions"]) == dict:
        up.update_project_status(str(project["_id"]), 1)
    else:
        up.update_project_status(str(project["_id"]), 1, sessions=sessions)
    return 1, {"simple_transcripts": simple_transcripts, "tscid_vidid": tscid_vidid}


def analyze_individual_tscs(project, incoming) -> tuple[int, dict]:
    # right now, this does the entirety of steps 2-4
    # analyze
    logger.debug("entered analyze_individual_tscs")
    question_list = project["questions"]
    project_id = incoming["projectId"]
    simple_transcripts = incoming["simple_transcripts"]
    tscid_vidid = incoming["tscid_vidid"]
    outgoing = mvp.map_reduce(question_list, simple_transcripts)

    # store findings in Findings collection
    findings = construct_findings(project_id, outgoing, tscid_vidid)
    findings_id = up.insert_findings(findings)

    up.update_project_status(str(project["_id"]), 2, findings_id=findings_id)
    logger.debug("exiting analyze_individual_tscs")
    return 2, {"individual_responses": outgoing}


def group_questions(project, incoming) -> tuple[int, dict]:
    """for expanding modularity. Grouping responses by question"""
    raise NotImplementedError
    outgoing = ...
    return 3, {"grouped_responses": outgoing}


def format_response(project, incoming) -> tuple[int, dict]:
    """for expanding modularity. Formatting the final response"""
    raise NotImplementedError
    outgoing = ...
    return 4, {"formatted_response": outgoing}


def timestamp_to_seconds(timestamp_str: str) -> float:
    hms = timestamp_str.split(sep=":")
    return 3600 * int(hms[0]) + 60 * int(hms[1]) + float(hms[2])


def construct_findings(id, markdown_content: str, transcript_video_dict) -> dict:
    logger.debug("entered construct_findings")
    response = md_to_json(markdown_content)

    response["projectId"] = id
    vid_count = len(transcript_video_dict)

    count = 5
    while (len(response["questions"]) == 0) and (count > 0):
        logger.debug(f"empty questions: {id}")
        response = md_to_json(markdown_content)
        count -= 1

    if len(response["questions"]) == 0:
        # TODO generate backup questions here
        logger.error('response["questions"] was empty')
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
                    logger.error(
                        "could not find "
                        + ("transcript" if tsc_id is None else "video")
                        + f'id for quote "{quote.get("quote", "")}"'
                    )

                # reformat timestamps (not needed now)
                # start = timestamp_to_seconds(quote.get("timestamp_start", "00:00:00.0"))
                # end = timestamp_to_seconds(quote.get("timestamp_end", "00:00:00.0"))
                # quote["timestamp_start"] = start
                # quote["timestamp_end"] = end

            theme["count"] = len(count_tracker)

    logger.debug("exiting construct_findings")
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
