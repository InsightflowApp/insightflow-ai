#!/usr/bin/env python3
# prompt_templates.py

#TODO all quotes for theme
#TODO theme description (see design Figma)

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
  'You will find the interview\'s file name at the top of the document. '
  'Begin with a new line, then the words '
  '"--- NEW INTERVIEW: <file name> ---" followed by '
  'another new line, then give a paragraph-long summary of the transcript. '
  'Then, answer the questions the following format:\n\n'

  'Question 1: <question 1>\n'
  'Relevant quotes from interviewee:\n'
  ' - "<relevant quote 1>"\n'
  ' - "<relevant quote 2>"\n'
  ' - "<relevant quote 3>"\n'
  '<...more quotes if relevant>\n'
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

  'Your response:\n'
) # map_template

# the template to take the best of map_template's responses and generalize
reduce_template = (
  'Hello! You are an interview helper whose goal is to synthesize '
  'the best answers to a list of questions by combining interviewee '
  'sentiments gotten from analyzing interview transcripts. You are to '
  'order the responses by the most common themes shared among interviews. '
  'That is to say, given a list of questions and a document of responses to '
  'these questions for each interview, please interpret the responses and '
  'list the most common findings (themes) for EACH QUESTION with supporting quotes. '
  'Note that each document contains a list of its interviewee\'s most frequent '
  ' points, which you may find helpful when constructing your answers. ' 
  'Answer EVERY QUESTION based only on the documents\' content. In the '
  'instructions, when you see angle brackets <like so>, take them as a '
  'field for you to fill. '
  'Here are the questions to answer:\n'
  '{questions}\n\n' # formatted as described, in a list

  # return the count on how many people answer these questions
  'First, count how many interviewees answered each question. '
  'Give a bulleted list of the questions and their answer count, '
  'ranked by highest answer count first. '
  'Then, please respond to these questions in your ranked order, '
  'and write your response in the following format:\n'
  '## Question 1: <question>\n'
  'Relevant quotes across interviews:\n'
  ' - <interview title A>:\n' 
  '   <bulleted list of at least 3 relevant quotes>'
  ' - <title B>:\n'
  '   <bulleted list of at least 3 relevant quotes>"\n'
  ' - <...same thing for all interviews>\n'
  '### Themes:\n'
  ' - Theme 1: <title reflecting most common response to the question> '
  '(<number of responses matching this theme>/<total interviews>)\n'
  '   - <title A>: <one quote from interview A>\n'
  '   - <title B>: <one quote from interview B>\n'
  '   - <...same thing for all interviews who answered with the theme>\n'
  ' * <describe this theme in 1 sentence. '
  'Example: Users reflect that the most time-consuming aspect of _X_ is _Y_.>\n'
  ' - Theme 2: <title reflecting second most common response> (<n/total>)\n'
  '   - <title C>: <one quote from interview C>\n'
  '   - <...same thing for all interviews who answered with the theme>\n'
  ' * <describe this theme in 1 sentence>'
  ' - Theme 3: <title reflecting third most common response> (<n/total>)\n'
  '   - <title D>: <one quote from interview D>\n'
  '   - <...same thing for all interviews who answered with the theme>\n'
  ' * <describe this theme in 1 sentence>'
  ' - <Theme...etc.>\n'
  '**Response:** <summary response to question based on all '
  'interviewees\' responses and your chosen quotes>\n\n'

  '...and so on. Please include quotes from every interview '
  'with a response, even if the quotes are repetitive. Try to include at least 3 '
  'unique themes per question, and please answer every question. '
  'The same quote can be used to support multiple themes. '
  'After providing these answers, give insights into the pain points '
  'you think your company should address, and why, as a bulleted list '
  'in a section named "Key Takeaways."\n'
  'Here are the responses to interviews, each delimited by the string '
  '"--- NEW INTERVIEW: <title> ---". The entire document is delimited by '
  'triple quotes ("""). Thanks for your help!\n\n'

  '"""{docs}"""\n\n'

  'Your response:\n'
) # reduce_template
