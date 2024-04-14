from typing import List


from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

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


class Quote(BaseModel):
    quote: str = Field(description="A quote used as a response to the question")
    speaker: str = Field(
        description="The speaker of the quote. Assume it's the interviewee"
    )
    timestamp_start: str = Field(
        description="The starting point of the quote",
        regex=r"\d+:\d+:\d+(\.\d+)?",
    )
    timestamp_end: str = Field(
        description="The ending point of the quote",
        regex=r"\d+:\d+:\d+(\.\d+)?",
    )
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
