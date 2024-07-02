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
    get_key_takeaways_summary,
)

from read_files.read_docs import read_pdf_from_url, read_docx_from_url

from server.logger import logger
from server.worker import connect_to_mqueue

"""
Receive logs from InsightFlow docs queue and process them.

This is the main file for handling text-like files. It handles RabbitMQ interactions, and 
performs actions on the project based on its phase.

For more information about each action, see update_project.py.
"""


def main():

    # TODO make args to handle log clearing
    # if clear-logs, call logger.clear()

    if "--clear-logs" in sys.argv:
        logger.info("cleared logs.")
        logger.clear()

    load_dotenv()

    global chan_name
    global project_status_table
    global LAST_STATUS

    chan_name = os.getenv("FILE_CHAN_NAME")

    # "projectStatus"
    # For projectStatus i, enact step i+1 until final status (LAST_STATUS) is reached.
    project_status_table = {
        0: transcribe_project,  # not started
        1: analyze_individual_tscs,  # transcripts done
        2: group_questions,  # individual analysis done
        3: get_json_response,  # grouping questions done
        4: get_key_takeaways_summary,  # json response done
        5: update_project,  # summarizing K.T. done
        # 6, all formatting done. Project sent to DB
    }

    LAST_STATUS = len(project_status_table)

    connect_to_mqueue()


# get doc content
def get_document_content(project, _) -> tuple[int, dict]:
    docs = list()
    for url_str, doc_name in project["sessions"].items():
        extension = os.path.splitext(doc_name)
        url = f"{os.getenv('INSIGHTFLOW_S3')}/{url_str}{extension}"
        doc = ""
        if extension == ".pdf":
            doc = read_pdf_from_url(url)
        else:
            # assume it's a word doc
            doc = read_docx_from_url(url)
        docs.append(doc)

    return 1, {"docs": docs}


# answer questions per page group
def answer_questions(project, incoming) -> tuple[int, dict]:
    pass


# group questions and generalize
def group_question_responses(project, incoming) -> tuple[int, dict]:
    pass


# format json response
def get_json_response(project, incoming) -> tuple[int, dict]:
    pass


# update
def update_project(project, incoming) -> tuple[int, dict]:
    pass
