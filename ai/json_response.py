from typing import List


from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI


def md_to_json(text) -> dict:
  model = ChatOpenAI(temperature=0)

  parser = JsonOutputParser(pydantic_object=Finding)

  prompt = PromptTemplate(
    template=reformat_template,
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
  )

  chain = prompt | model | parser
  
  response = chain.invoke({"text": text})
  response['markdownContent'] = text

  return response


class Quote(BaseModel):
  quote: str = Field(description="A quote used as a response to the question")
  speaker: str = Field(description="The speaker of the quote. Assume it's the interviewee")
  timestamp: str = Field(description="The starting point of the quote")
  transcript_id: str = Field(description="The name of the quote's transcript")


class Theme(BaseModel):
  theme: str = Field(description="The response to the question")
  quotes: List[Quote] = Field(description="Quotes supporting the theme as a response to the question")
  count: int = Field(description="Number of participants who shared this theme.")
  total: int = Field(description="Total number of participants")


class Question(BaseModel):
  question: str = Field(description="The question that was asked")
  themes: List[Theme] = Field(description="All of the themes written in response to this question")
  analysis: str = Field(description="The answer(s) to this question, looking at all of the themes")


class Finding(BaseModel):
  questions: List[Question] = Field(description="All of the questions asked")
  keyTakeaways: List[str] = Field(description="A list of insights into the pain points you think the company should address, and why")


reformat_template = (
  "Hi! Please reformat this response, and add key takeaways:\n\n"
  "{text}\n\n"
  "{format_instructions}\n"
)

