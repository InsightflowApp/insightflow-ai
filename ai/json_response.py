from typing import List


from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

import db.user_projects as up

import time

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

    # add timestamps to quotes
    for question in response["questions"]:
        for theme in question["themes"]:
            for quote in theme["quotes"]:
                quote["timestamp_start"], quote["timestamp_end"] = find_times(quote)

    return response


"""
response format:
{
    "questions": [
        "question": string,
        "themes": [
            "theme": string
            "quotes": [
                "quote": string
                "speaker": string
                "timestamp_start": string
                "timestamp_end": string
                "transcript_id": string
            ]
        ],
        "analysis": string,
    ],
    "keyTakeaways": [string],
}
"""


def find_times(quote) -> tuple[float, float]:
    """
    Find the start and end times of a quote with a given Quote object
    quote: quote, speaker, transcript_id

    returns tuple(start timestamp, end timestamp)
    """
    # TODO add speaker to quote info

    transcript = up.get_transcript(quote["transcript_id"])

    cursor, start_ts, end_ts = 0, -1.0, 0.0

    for para in transcript["paragraphs"]["paragraphs"]:
        for sentence in para["sentences"]:
            cursor, start_ts, end_ts = match(cursor, quote, sentence, start_ts)
            if cursor == len(quote["quote"]):
                break

    if cursor == len(quote["quote"]):
        return start_ts, end_ts

    print("could not find exact quote in transcript")

    return start_ts, end_ts


def match(pos, quote, sentence, start: float = -1.0) -> tuple[int, float, float]:
    """
    match the quote up with the sentence, adding proper timestamps to quote if necessary
    pos: index previously matched
    quote: quote object

    returns tuple(new_pos, start, end), 0 -1., 0. if not found
    """
    q = quote["quote"]

    search_space = min(len(q) - pos, len(sentence["text"]))
    if start == -1.0:
        start = sentence["start"]

    for i in range(search_space):
        if q[i + pos] != sentence["text"][i]:
            return 0, -1.0, 0.0

    new_cursor = pos + search_space

    if new_cursor == len(q):
        return new_cursor, start, sentence["end"]

    return new_cursor + 1, start, 0.0  # add 1 for missing space between sentences


class Quote(BaseModel):
    quote: str = Field(description="A quote used as a response to the question")
    speaker: str = Field(
        description="The speaker of the quote. Assume it's the interviewee"
    )
    # timestamp_start: str = Field(
    #     description="The starting point of the quote",
    #     regex=r"\d+:\d+:\d+(\.\d+)?",
    # )
    # timestamp_end: str = Field(
    #     description="The ending point of the quote",
    #     regex=r"\d+:\d+:\d+(\.\d+)?",
    # )
    transcript_id: str = Field(
        description="The ID of the quote's transcript", regex=r"\d+"
    )


class Theme(BaseModel):
    theme: str = Field(description="The response to the question")
    quotes: List[Quote] = Field(
        description="Quotes supporting the theme as a response to the question"
    )
    # count: int = Field(description="Number of quotes.")
    # total: int = Field(description="Total number of transcripts")


class Question(BaseModel):
    question: str = Field(description="The question that was asked")
    themes: List[Theme] = Field(
        description="All of the themes written in response to this question"
    )
    analysis: str = Field(
        description="The answer(s) to this question, looking at all of the themes"
    )


class Finding(BaseModel):
    questions: List[Question] = Field(
        description="question objects corresponding to EACH of the given responses"
    )
    keyTakeaways: List[str] = Field(
        description=(
            "A list of insights into the pain points you think the company "
            + "should address, and why. The items combined should be 100 words or "
            + "less."
        )
    )


reformat_template = (
    "Hi! Please reformat this response, and add key takeaways:\n\n"
    "{text}\n\n"
    "{format_instructions}\n"
)
