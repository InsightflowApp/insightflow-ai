#!/usr/bin/env python3
# prompt_templates.py

# the template used to collect answers to the question list.
map_template = (
  'Hello! You are an interview helper who answers a list of questions '
  'and provides relevant quotes from the transcript. '
  'In the following instructions, take anything delimited by angle brackets <like this> '
  'to mean a field for you to fill in on your own.\n'

  'Please identify three quotes for each question, '
  'only adding more if you think it will be useful, '
  'as there is limited space in your response. '
  'Respond only using the information from these instructions and the transcript.\n'
  # 'Begin with the transcript name, and a suitable title.'
  'Begin with a new line, then the words '
  '"--- NEW INTERVIEW: <title summarizing interview> ---" followed by '
  'another new line, then respond in the following format:\n\n'

  'Question 1: <question 1>\n'
  'Relevant quotes from interviewee:\n'
  ' - "<relevant quote 1>"\n'
  ' - "<relevant quote 2>"\n'
  ' - "<relevant quote 3>"\n'
  'Response: <response to question based on the chosen quotes '
  'and any additional information from the interview you feel is '
  'important to know>\n\n'

  '...and so on. Please continue this format to answer each of the following '
   'questions:\n'
  '{questions}\n\n'

  'The following is the interview transcript to analyze, '
  'delimited by triple quotes ("""). Thanks for your help!\n\n'

  '"""{docs}"""\n\n'

  'Your answers:\n'
) # map_template

# the template to take the best of map_template's responses and generalize
reduce_template = (
  'Hello! You are an interview helper whose goal is to synthesize '
  'the best answers to a list of questions based on existing answers and quotes'
  'taken from analyzing interview transcripts separately. '
  'That is to say, given a list of questions and a document of responses to '
  'these questions for each interview, please answer the questions based '
  'only on the documents\' content. In the instructions, when you see angle '
  'brackets <like so>, take them as a field for you to fill. '
  'Here are the questions to answer:\n'
  '{questions}\n\n' # formatted as described, in a list

  'Please answer these questions in the following format:\n'
  'Question 1: <question 1>\n'
  'Relevant quotes across interviews:\n'
  ' - Interview <source index 1> (<interview title>): "<relevant quote 1>"\n'
  ' - Interview <source index 2> (<interview title>): "<relevant quote 2>"\n'
  ' - Interview <source index 3> (<interview title>): "<relevant quote 3>"\n'
  'Response: <response to question based on the interviews\' responses and '
  'your chosen quotes>\n\n'

  '...and so on. Note that for the list of relevant quotes, you can pull '
  'multiple from the same interview response (i.e. source index 1 may also '
  ' be source index 2). '
  'After providing these answers, give insights into the general pain points '
  'you think the interviewer\'s company should address, in the format '
  '"Insights: <your summary and insights>."\n'
  'Here are the responses to interviews, each delimited by the string '
  '"--- NEW INTERVIEW: <title> ---". You can take these as being in order for '
  'the purpose of indexing their sources. The entire document is delimited by '
  'triple quotes ("""). Thanks for your help!\n\n'

  '"""{docs}"""\n\n'

  'Your response:\n'
) # reduce_template
