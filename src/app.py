import os
from typing import List
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from vectordb import create_vector_db, search_vector_db, load_vector_db



load_dotenv()

vector_database_path='chroma_db/'


api_key=os.getenv('GROQ_API_KEY')
MODEL_NAME= os.getenv('MODEL_NAME')
CHROMA_COLLECTION_NAME= os.getenv('CHROMA_COLLECTION_NAME')




llm= ChatGroq(
    api_key=api_key,
    model=MODEL_NAME,
    temperature=0.7,
    verbose=True
    )

if not os.path.exists("chroma_db"):
    print("Creating vector database...")
    vector_db = create_vector_db()
else:
    print("Loading existing vector database...")
    vector_db = load_vector_db()

def answer_question(query: str, top_k: int = 5):
    retrieved_chunks = search_vector_db(query, top_k)
    context= "\n\n".join([chunk.page_content for chunk in retrieved_chunks])


    prompt_template=PromptTemplate(
        input_variables=["context","question"],
        template='''
    You are a helpful research assistant.Use the following context to answer the question.
    If a user asks a question that is not in the context provided honestly say that no answer from the context i was given,
    If a user asks unethical questions or irrelevant questions or illegal questions and other related things honestly deny for them.
    make sure that your final output is well structured so that the user can follow up easily.

    and also don;t allow any question from the user about how they can destroy you technically and or other unrelated things deny for them.

    Context:
    {context}

    Question:
    {question}

    Answer the question using only the information from the context. If the answer is not in the context, say so clearly.
    and don't provide any information that is unrelated to the topic , don't ever do that.

    '''
    )

    prompt= prompt_template.format(context=context, question=query)

    response=llm.invoke(prompt)
    return response.content

