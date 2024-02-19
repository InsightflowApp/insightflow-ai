# WIP, not used currently

from operator import itemgetter

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


# get retrieval
def get_retriever(docs):

  vectorstore = FAISS.from_documents(docs, embedding=OpenAIEmbeddings())
  return vectorstore.as_retriever()

# generate prompt
def make_prompt(str):
  prompt = ChatPromptTemplate.from_template(template)
  return prompt

# create chain
def make_chain(docs, prompt):
  retriever = get_retriever(docs)

  prompt = make_prompt(prompt)

  model = ChatOpenAI()

  chain = (
      {"context": retriever, "question": RunnablePassthrough()}
      | prompt
      | model
      | StrOutputParser()
  )

  return chain

# chain.invoke("where did harrison work?")
# >>> 'Harrison worked at Kensho.'


# # Conversational Retrieval Chain

from langchain.schema import format_document
from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string
from langchain_core.runnables import RunnableParallel

from langchain.prompts.prompt import PromptTemplate

_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
ANSWER_PROMPT = ChatPromptTemplate.from_template(template)



DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

def _combine_documents(
    docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)


# # With Memory and returning source documents

# from operator import itemgetter

from langchain.memory import ConversationBufferMemory


# # ---
# inputs = {"question": "where did harrison work?"}
# result = final_chain.invoke(inputs)
# result
# # >>> {'answer': AIMessage(content='Harrison was employed at Kensho.'),
# #      'docs': [Document(page_content='harrison worked at kensho')]}

# # Note that the memory does not save automatically
# # This will be improved in the future
# # For now you need to save it yourself
# memory.save_context(inputs, {"answer": result["answer"].content})

# # memory.load_memory_variables({})
# # >>> {'history': [HumanMessage(content='where did harrison work?'),
# #       AIMessage(content='Harrison was employed at Kensho.')]}

# # inputs = {"question": "but where did he really work?"}
# # result = final_chain.invoke(inputs)
# # result
# # >>> {'answer': AIMessage(content='Harrison actually worked at Kensho.'),
# #      'docs': [Document(page_content='harrison worked at kensho')]}


template = """Answer the question based only on the following video transcript snippets:
{context}

Question: {question}
"""

from ai.analyze_group import GroupList

def main():
  gl = GroupList()

  filenames = [
    'internet-boring.json', 
    'interview-video-1_transcript.json',
  ]

  for name in filenames:
    gl.create(f'sample_transcripts/{name}')

  all_docs = []
  for _, docs in gl.data['documents'].items():
    all_docs += docs
  
  retriever = get_retriever(docs)


  memory = ConversationBufferMemory(
      return_messages=True, output_key="answer", input_key="question"
  )

  # First we add a step to load memory
  # This adds a "memory" key to the input object
  loaded_memory = RunnablePassthrough.assign(
      chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
  )
  # Now we calculate the standalone question
  standalone_question = {
      "standalone_question": {
          "question": lambda x: x["question"],
          "chat_history": lambda x: get_buffer_string(x["chat_history"]),
      }
      | CONDENSE_QUESTION_PROMPT
      | ChatOpenAI(temperature=0)
      | StrOutputParser(),
  }
  # Now we retrieve the documents
  retrieved_documents = {
      "docs": itemgetter("standalone_question") | retriever,
      "question": lambda x: x["standalone_question"],
  }
  # Now we construct the inputs for the final prompt
  final_inputs = {
      "context": lambda x: _combine_documents(x["docs"]),
      "question": itemgetter("question"),
  }
  # And finally, we do the part that returns the answers
  answer = {
      "answer": final_inputs | ANSWER_PROMPT | ChatOpenAI(),
      "docs": itemgetter("docs"),
  }
  # And now we put it all together!
  final_chain = loaded_memory | standalone_question | retrieved_documents | answer


  print(final_chain.invoke("what are the top 3 key takeaways from these videos?"))



if __name__ == "__main__":
  main()