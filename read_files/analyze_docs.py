#!/usr/bin/env python3
# analyze_docs.py

from ai.mvp import get_LLM
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


# perhaps
# def get_entire_document_summary():


def answer_questions_with_doc(
    question_list: list[str],
    docs: list[str],
) -> list[str]:
    """
    calls LLM to answer a list of questions for each transcript provided.

    :param question_list: a list of questions, formatted with numbers already
    :param transcripts: a list of each transcript's contents, as strings
    """
    questions: str = "\n".join(question_list)

    prompt = PromptTemplate(
        template=answer_questions_with_doc_template,
        input_variables=["docs"],
        partial_variables={"questions": questions},
    )

    chain = {"docs": RunnablePassthrough()} | prompt | get_LLM() | StrOutputParser()

    tscs = list(map(Document, docs))

    return chain.batch(tscs)


def group_answers_per_response(question_list: list[str], responses: str) -> list[str]:
    """
    answer each question based on all the transcripts' responses.
    """

    prompt = PromptTemplate(
        template=group_an_answer_template,
        input_variables=["question"],
        partial_variables={"docs": responses},
    )

    chain = {"question": RunnablePassthrough()} | prompt | get_LLM() | StrOutputParser()

    return chain.batch(question_list)



# the template used to collect answers to the question list.
# inputs: questions, docs
answer_questions_with_doc_template = (
    "Hello! You are an document analysis helper who answers a list of questions "
    "and provides relevant quotes based on a document. "
    "In the following instructions, take anything delimited by angle brackets "
    "<like this> to mean a field for you to fill in on your own.\n"
    "Please identify three quotes for each question if possible, "
    "as there is limited space in your response. "
    "Do not add more information from your side, "
    "and do not summarise the quotes, state the exact words of the user. "
    "Respond only using the information from these instructions and the given text.\n"
    # 'Begin with the transcript name, and a suitable title.'
    "You will find the text's file name at the top. "
    "Begin with a new line, then the words "
    '"--- NEW DOCUMENT SECTION: <document section ID> ---" followed by '
    "another new line, then give a paragraph-long summary of the text. "
    "Then, answer ALL questions using the following format:\n\n"
    "Question 1: <question 1>\n"
    "Relevant quotes from document section (document <document section ID>):\n"
    ' - "<relevant quote 1>"\n'
    ' - "<relevant quote 2>"\n'
    ' - "<relevant quote 3>"\n'
    "<...more quotes if relevant>\n"
    "Response: <response to question based on the chosen quotes "
    "and any additional information from the text you feel is "
    "important to know>\n\n"
    "...and so on. Note that you can combine multiple fragments of a quote "
    "into one if they are separated by timestamps. Be sure to update the timestamp "
    "accordingly if this is done.\n"
    "If the document section does not answer the question, omit it."
    "Please continue this format to answer each of the following "
    "questions:\n"
    "{questions}\n\n"
    "After answering all questions, please provide the most commonly mentioned points "
    "from the document as a list. "
    "The following is the document section to analyze, "
    'delimited by triple quotes ("""). Thanks for your help!\n\n'
    '"""{docs}"""\n\n'
    "Your response:\n"
)  # map_template

# the template to take the best of map_template's responses and generalize
# inputs: question, docs
group_an_answer_template = (
    "Hello! You are a document analysis helper whose goal is to extract "
    "meaningful responses to a particular question from a document of answers. You are to "
    "order your responses by the most common themes shared among groups of answers, "
    "and provide exact quotes from the answer documents without any summarization "
    "or modification of their words. "
    "Do not summarize, rephrase, or change the words of the user in any quote. "
    "Return the exact words as they appear in the transcripts. "
    "If you cannot find the exact words to the answer to your question, "
    "return the words that most closely match your meaning."
    "But DO NOT summarise anything the user says. "
    "Give ONLY the EXACT words of the answer documents. "
    "Answer YOUR QUESTION based only on the documents' content. In the instructions, when you see angle brackets "
    "<like so>, take them as a field for you to fill."
    "Here is the question to answer:\n"
    "{question}\n\n"
    "Please respond to these questions with multiple answers, called themes, "
    "in the following format:\n"
    "## Question <i>: <question>\n"
    "### Themes:\n"
    " - Theme 1: <short title reflecting most common response to the question, "
    "6 words or less>\n"
    "   - <transcript ID A> (<timestamp>): <exact quote from document A>\n"
    "   - <transcript ID B> (<timestamp>): <exact quote from document B>\n"
    "   - <...same thing for ALL DOCUMENTS WITH RESPONSES MATCHING THIS THEME>\n"
    " - Theme 2: <short title reflecting second most common response>\n"
    "   - <transcript ID C> (<timestamp>): <exact quote from document C>\n"
    "   - <...same thing for ALL document responses matching this theme>\n"
    " - Theme 3: <short title reflecting third most common response>\n"
    "   - <transcript ID D> (<timestamp>): <exact quote from document D>\n"
    "   - <...same thing for ALL document responses matching this theme>\n"
    " - <Theme...etc.>\n"
    "**Response:** <summary response to question based on all responses and your chosen quotes in 50 "
    "words or less>\n\n"
    "Please include quotes from every document section with a response, even if the "
    "quotes are repetitive. Try to include at least 3 unique themes. "
    "Theme titles should be 6 words or less. The same quote can be used to support multiple themes. "
    "Please be sure to include the timestamps for your chosen quotes."
    "Here are the responses to documents, each delimited by the string "
    '"--- NEW DOCUMENT SECTION: <document section ID> ---". The entire document is delimited by '
    'triple quotes ("""). Thanks for your help!\n\n'
    '"""{docs}"""\n\n'
    "Your response:\n"
)  # reduce_template


summarize_key_takeaways_template = (
    "Hello! You are a document analysis helper whose goal is to summarize "
    "the key takeaways of already-analyzed texts in two sentences. "
    "You will be given the entire analysis for context, but please "
    "summarize ONLY the Key Takeaways section. Here is the document, "
    "delimited by triple-quotes:\n\n"
    '"""{doc}"""\n\n'
    "Your two-sentence summary of Key Takeaways:\n"
)
