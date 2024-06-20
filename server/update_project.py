import os

from db import user_projects as up

from transcribe.transcribe_async import transcribe_urls
from ai.mvp import answer_per_transcript, question_transcript_wide
from ai.json_response import md_to_json

from server.logger import logger

"""
Update the project depending on its status.

For status i, enact step i+1 until final status is reached:

Phase 0: project has had all videos and questions uploaded.
Action to take: transcribe_project

Phase 1: videos in the project have been transcribed, and transcripts have been stored.
Action to take: analyze_individual_tscs

Phase 2: each transcript has had the questions answered about it.
Action to take: group_questions

Phase 3: responses to each question have been grouped and answered project-wide.
Action to take: format_response

Phase 4: responses have been formatted to JSON and are ready to be used by frontend.
Action to take: None
"""


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
    logger.debug(
        "entered transcribe_project",
        f"project keys: {project.keys()}",
        f"sessions type: {type(project['sessions'])}",
        sep="\n\t",
    )
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
    transcripts = transcribe_urls(audio_urls)
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
    simple_transcripts = incoming["simple_transcripts"]
    outgoing: list[str] = answer_per_transcript(
        question_list=question_list, transcripts=simple_transcripts
    )
    # outgoing = mvp.map_reduce(question_list, simple_transcripts)

    # up.update_project_status(str(project["_id"]), 2)
    logger.debug("exiting analyze_individual_tscs")
    return 2, {"individual_responses": outgoing, "tscid_vidid": incoming["tscid_vidid"]}


def group_questions(project, incoming) -> tuple[int, dict]:
    """for expanding modularity. Grouping responses by question"""
    logger.debug("entered group_questions")

    question_list = project["questions"]
    individual_tsc_responses = "\n\n".join(incoming["individual_responses"])

    outgoing: list[str] = question_transcript_wide(
        question_list=question_list, responses=individual_tsc_responses
    )

    # up.update_project_status(str(project["_id"]), 3)

    logger.debug("exiting group_questions")

    return 3, {"grouped_responses": outgoing, "tscid_vidid": incoming["tscid_vidid"]}


def format_response(project, incoming) -> tuple[int, dict]:
    """for expanding modularity. Formatting the final response"""
    project_id = incoming["projectId"]
    tscid_vidid = incoming["tscid_vidid"]

    # store findings in Findings collection
    outgoing = construct_findings(
        project_id, "\n\n".join(incoming["grouped_responses"]), tscid_vidid
    )
    findings_id = up.insert_findings(outgoing)

    up.update_project_status(str(project["_id"]), 2, findings_id=findings_id)

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
        try:
            raise AttributeError("could not convert questions to json")
        except AttributeError as e:
            logger.error('response["questions"] was empty', exception=e)
            raise

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
