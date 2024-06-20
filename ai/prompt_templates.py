#!/usr/bin/env python3
# prompt_templates.py

# TODO all quotes for theme

# the template used to collect answers to the question list.
# inputs: questions, docs
map_template = (
    "Hello! You are an interview helper who answers a list of questions "
    "and provides relevant quotes from the transcript. "
    "In the following instructions, take anything delimited by angle brackets "
    "<like this> to mean a field for you to fill in on your own.\n"
    "Please identify three quotes AND their corresponding starting timestamps, "
    "for each question if possible, "
    #"only adding more if you think it will be useful, "
    "as there is limited space in your response. "
    "Do not add more information from your side,"
    "and do not summarise the quotes, state the exact words of the user."
    "Respond only using the information from these instructions and the transcript.\n"
    # 'Begin with the transcript name, and a suitable title.'
    "You will find the interview's file name at the top of the document. "
    "Begin with a new line, then the words "
    '"--- NEW INTERVIEW: <transcript ID> ---" followed by '
    "another new line, then give a paragraph-long summary of the transcript. "
    "Then, answer the questions the following format:\n\n"
    "Question 1: <question 1>\n"
    "Relevant quotes from interviewee (transcript <transcript ID>):\n"
    ' - (<timestamp start> --> <timestamp end>): "<relevant quote 1>"\n'
    ' - (<timestamp start> --> <timestamp end>): "<relevant quote 2>"\n'
    ' - (<timestamp start> --> <timestamp end>): "<relevant quote 3>"\n'
    "<...more quotes if relevant>\n"
    "Response: <response to question based on the chosen quotes "
    "and any additional information from the interview you feel is "
    "important to know>\n\n"
    "...and so on. Note that you can combine multiple fragments of a quote "
    "into one if they are separated by timestamps. Be sure to update the timestamp "
    "accordingly if this is done.\n"
    "If the interviewee does not answer the question, omit it."
    "Please continue this format to answer each of the following "
    "questions:\n"
    "{questions}\n\n"
    "After answering all questions, please provide the most commonly mentioned points "
    "from the interviewer as a list. "
    "The following is the interview transcript to analyze, "
    'delimited by triple quotes ("""). Thanks for your help!\n\n'
    '"""{docs}"""\n\n'
    "Your response:\n"
)  # map_template

# the template to take the best of map_template's responses and generalize
# inputs: question, docs
reduce_template = (
    "Hello! You are an interview helper whose goal is to extract "
    "the exact words from interview transcripts. You are to "
    "order the responses by the most common themes shared among interviews, "
    "and provide the exact quotes from the interviewees without any summarization "
    "or modification of their words."
    
    "For each response, find the exact user quotes for each video which contains the exact words the user mentioned. "
    "Do not summarize, rephrase, or change the words of the user in any quote. Return the exact words as they appear "
    "in the transcripts."
    "Note that each document contains a list of its interviewee's most frequent points, which you may find helpful "
    "when constructing your answer."
    "Answer YOUR QUESTION based only on the documents' content. In the instructions, when you see angle brackets "
    "<like so>, take them as a field for you to fill."
    "Here is the question to answer:\n"
    "{question}\n\n"
    
    "Please respond to these questions with multiple answers, called themes, "
    "in the following format:\n"
    "## Question <i>: <question>\n"
    "### Themes:\n"
    " - Theme 1: <short title reflecting most common response to the question, 6 words or less>\n"
    "   - <transcript ID A> (<timestamp>): <exact quote or conversation from interview A>\n"
    "   - <transcript ID B> (<timestamp>): <exact quote from interview B>\n"
    "   - <...same thing for ALL INTERVIEWS WITH RESPONSES MATCHING THIS THEME>\n"
    " * <describe this theme in 1 sentence, e.g. "
    '"Users reflect that the most time-consuming aspect of _X_ is _Y_.">\n'
    " - Theme 2: <short title reflecting second most common response>\n"
    "   - <transcript ID C> (<timestamp>): <exact quote from interview C>\n"
    "   - <...same thing for ALL interview responses matching this theme>\n"
    " * <describe this theme in 1 sentence>\n"
    " - Theme 3: <short title reflecting third most common response>\n"
    "   - <transcript ID D> (<timestamp>): <exact quote from interview D>\n"
    "   - <...same thing for ALL interview responses matching this theme>\n"
    " * <describe this theme in 1 sentence>\n"
    " - <Theme...etc.>\n"
    "**Response:** <summary response to question based on all interviewees' responses and your chosen quotes in 50 "
    "words or less>\n\n"
    "Please include quotes from every interview with a response, even if the quotes are repetitive. Try to include at "
    "least 3 unique themes."
    "Theme titles should be 6 words or less. The same quote can be used to support multiple themes. "
    "Please be sure to include the timestamps for your chosen quotes."
    "Here are the responses to interviews, each delimited by the string "
    '"--- NEW INTERVIEW: <transcript ID> ---". The entire document is delimited by '
    'triple quotes ("""). Thanks for your help!\n\n'
    '"""{docs}"""\n\n'
    "Your response:\n"
)  # reduce_template
