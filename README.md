# Kepler College Student Handbook RAG Assistant

This project is an AI-powered **Retrieval-Augmented Generation (RAG)** assistant built using **LangChain**, **Chroma**, and **Streamlit**.  
It enables users to ask natural language questions about the **Kepler College Student Handbook** and receive accurate, context-grounded answers sourced strictly from the handbook content.

The system demonstrates a practical application of RAG in an educational environment by combining semantic document retrieval with controlled language model generation.

---

## Features

- Context-aware answers derived only from the official student handbook  
- Semantic retrieval using a Chroma vector database  
- LLM-powered answer generation via Groq API (LLaMA 3)  
- Interactive Streamlit web interface  
- Modular architecture separating retrieval logic, vector storage, and UI  
- Secure configuration using environment variables  

---

## System Architecture (RAG Pipeline)

The assistant follows a standard Retrieval-Augmented Generation workflow:

1. The Kepler Student Handbook is loaded and preprocessed.  
2. The document is split into overlapping text chunks.  
3. Each chunk is embedded and stored in a Chroma vector database.  
4. User queries are embedded at runtime.  
5. The vector database retrieves the top-k most relevant chunks.  
6. Retrieved context is injected into a prompt template and passed to the LLM for answer generation.

> A system architecture diagram can be included in the Ready Tensor publication to visually illustrate this flow.

---

## Text Chunking Strategy

To balance retrieval accuracy and contextual completeness, the following chunking strategy is used:

- **Chunk size:** approximately 500 tokens  
- **Chunk overlap:** approximately 50 tokens  

**Rationale:**
- Smaller chunks improve retrieval precision.
- Overlap preserves semantic continuity across sections.
- This reduces context loss during retrieval.

---

## Query Processing

User queries are handled as follows:

- Input validation and normalization  
- Conversion of the query into vector embeddings  
- Similarity search against stored document embeddings  
- Retrieval of the top-k most relevant chunks  
- Context injection into a structured prompt for response generation  

This process ensures generated answers remain grounded in the handbook content.

---

## Retrieval Evaluation

Retrieval quality was evaluated using manual inspection and relevance checks, which is appropriate for an early-stage RAG system.

**Evaluation criteria:**
- Relevance of retrieved chunks  
- Accuracy of generated answers  
- Absence of hallucinated content  
- Coverage of handbook-specific policies  

**Sample evaluation:**

| Query | Retrieval Quality | Answer Accuracy |
|------|------------------|----------------|
| Graduation requirements | High | Correct |
| Attendance policy | High | Correct |

Future improvements may include automated metrics such as recall@k or embedding similarity thresholds.

---

## Project Structure

```text
rt-aaidc-project1-template1/
├── src/
│   ├── app.py            # Core RAG logic
│   ├── vectordb.py       # Vector database creation and retrieval
│   ├── streamlit.py      # Streamlit user interface
│   └── images/           # Architecture diagrams (optional)
├── data/
│   └── Kepler College_Student Handbook.txt
├── .env
├── requirements.txt
├── README.md


nstallation and Setup
1. Clone the repository
git clone https://github.com/<your-username>/<your-project-name>.git
cd <your-project-name>

2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Configure environment variables

Create a .env file and add:

GROQ_API_KEY=your_api_key_here
MODEL_NAME=llama3-8b-8192
CHROMA_COLLECTION_NAME=my_collection


If using a different LLM provider (e.g., OpenAI), update both the API key and model name accordingly.

Running the Application
streamlit run src/streamlit.py


Once running, open the local URL in your browser and begin asking questions about the handbook.

Example Test Query
What is this publication about?


This query can be used to validate retrieval relevance and response grounding.

Project Scope

Designed specifically for Kepler College Student Handbook question answering

Not intended for open-domain or general-purpose queries

Relies on the completeness and accuracy of the provided handbook

Limitations and Future Work

Current limitations:

Manual retrieval evaluation

Single-document knowledge base

No reranking or feedback loop

Planned improvements:

Automated retrieval evaluation metrics

Support for multiple documents

Query rewriting and reranking

Enhanced UI and feedback collection

Configuration Summary
Variable	Description
GROQ_API_KEY	API key for Groq LLM access
MODEL_NAME	Language model used
CHROMA_COLLECTION_NAME	Vector database collection name
Author

HARERIMANA Honore
Business Analyst and Machine Learning Engineer