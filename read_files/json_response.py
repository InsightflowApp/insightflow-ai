from typing import List


from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from datetime import timedelta

import db.user_projects as up

import time

from ai.json_response import Finding, reformat_template

# TODO consider making a backup response, based on a parser


def md_to_json(text) -> dict:
    model = ChatOpenAI(temperature=0)

    parser = JsonOutputParser(pydantic_object=Finding)

    prompt = PromptTemplate(
        template=reformat_template,
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | model | parser

    print("md_to_json: starting")
    time_1 = time.time()

    response = chain.invoke({"text": text})

    time_2 = time.time()
    print(f"md_to_json: done. Time: {time_2 - time_1} seconds")

    # add key takeaways to markdown response
    key_takeaways = "\n\n## Key Takeaways"
    for point in response["keyTakeaways"]:
        key_takeaways += f"\n- {point}"

    response["markdownContent"] = text + key_takeaways

    # print(f"{response=}")

    # add timestamps to quotes
    for question in response["questions"]:
        for theme in question["themes"]:
            for quote in theme["quotes"]:
                quote["doc_id"] = quote["transcript_id"]
                del quote["transcript_id"]

    return response


# response format:
# {
#     "questions": [
#         "question": string,
#         "themes": [
#             "theme": string
#             "quotes": [
#                 "quote": string
#                 "speaker": string
#                 "doc_id": string
#             ]
#         ],
#         "analysis": string,
#     ],
#     "keyTakeaways": [string],
# }
