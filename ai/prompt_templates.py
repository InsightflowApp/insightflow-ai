#!/usr/bin/env python3
# prompt_templates.py

# the template used to collect answers to the question list.
map_template = (
  'Hello! You are an interview helper who answers a list of questions '
  'and provides relevant quotes from the transcript. '
  'In the following instructions, take anything delimited by angle brackets <like this> '
  'to mean a field for you to fill in on your own.\n'

  'Please identify three quotes for each question if possible, '
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

  '...and so on. If the interviewee does not answer the question, omit it.'
  'Please continue this format to answer each of the following '
   'questions:\n'
  '{questions}\n\n'

  'After answering all questions, please provide the most commonly mentioned points '
  'from the interviewer as a list. '
  'The following is the interview transcript to analyze, '
  'delimited by triple quotes ("""). Thanks for your help!\n\n'

  '"""{docs}"""\n\n'

  'Your answers:\n'
) # map_template

# the template to take the best of map_template's responses and generalize
reduce_template = (
  'Hello! You are an interview helper whose goal is to synthesize '
  'the best answers to a list of questions by combining interviewee '
  'sentiments gotten from analyzing interview transcripts. You are to '
  'order the questions you respond to by the number of interviewees that '
  'responded to them. '
  'That is to say, given a list of questions and a document of responses to '
  'these questions for each interview, please interpret the responses and list '
  'the most common answers with supporting quotes. Answer the questions based '
  'only on the documents\' content. In the instructions, when you see angle '
  'brackets <like so>, take them as a field for you to fill. '
  'Here are the questions to answer:\n'
  '{questions}\n\n' # formatted as described, in a list

  # return the count on how many people answer these questions
  'First, count how many interviewees answered each question. '
  'Give a bulleted list of the questions and their answer count, '
  'ranked by highest answer count first. '
  'Then, please respond to these questions in your ranked order, '
  'and write your answers in the following format:\n'
  'Theme 1: <question 1 rewritten as a theme>\n'
  'Relevant quotes across interviews:\n'
  ' - Interview <source index 1> (<interview title>)\n' 
  '   - "<relevant quote 1>"\n'
  '   - "<relevant quote 2>"\n'
  ' - Interview <source index 2> (<interview title>)\n'
  '   - "<relevant quote 1>"\n'
  '   - <...>\n'
  ' - <...>\n'
  'Response: <response to question based on all interviewees\' responses and '
  'your chosen quotes>\n\n'

  '...and so on. You do not have to include quotes from every interview '
  'with a response, if the quotes are repetitive.'
  'After providing these answers, give insights into the pain points '
  'you think your company should address, and why, as a bulleted list.\n'
  'Here are the responses to interviews, each delimited by the string '
  '"--- NEW INTERVIEW: <title> ---". You can take these as being in order for '
  'the purpose of indexing their sources. The entire document is delimited by '
  'triple quotes ("""). Thanks for your help!\n\n'

  '"""{docs}"""\n\n'

  'Your response:\n'
) # reduce_template
