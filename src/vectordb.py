import os
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data")







vector_database_path='chroma_db/'

embeddings= HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

def load_documents():   
    for file_name in os.listdir(DATA_PATH):
        path=os.path.join(DATA_PATH,file_name)
        loader= TextLoader(path,encoding='utf-8')
        documents=loader.load()
        return documents
    
def split_documents(documents):
    
    text_splitter= RecursiveCharacterTextSplitter(
        
        chunk_size= 1000,
        chunk_overlap=50
    )

    chunks= text_splitter.split_documents(documents)
    print(f"split into {len(chunks)} chunks")
    return chunks


def create_vector_db():
    documents=load_documents()
    chunks=split_documents(documents)
    vector_db=Chroma.from_documents(chunks,embeddings,persist_directory=vector_database_path)
    vector_db.persist()
    return vector_db

def load_vector_db():
    vector_db=Chroma(persist_directory=vector_database_path,embedding_function=embeddings)
    return vector_db

def search_vector_db(query,top_k=5):
    vector_db=load_vector_db()
    results= vector_db.similarity_search(query,top_k)
    return results



    






