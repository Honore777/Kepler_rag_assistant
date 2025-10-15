# 🧠 Kepler College Student Handbook RAG Assistant

This project is an AI-powered **Retrieval-Augmented Generation (RAG)** assistant built using **LangChain**, **Chroma**, and **Streamlit**.  
It allows users to ask questions about the *Kepler College Student Handbook*, and receive accurate, context-based answers derived directly from the document — ensuring reliability and factual integrity.

---

## 🚀 Features

- 📘 Context-based answers sourced only from the official student handbook  
- 🧩 Vector database using **Chroma** for efficient retrieval  
- 🤖 LLM integration via **Groq API** for structured, human-like responses  
- 💬 Easy-to-use **Streamlit** web interface  
- ⚙️ Modular design — separated logic (`app.py`), data (`vectordb.py`), and UI (`streamlit.py`)

---

## 📂 Project Structure

rt-aaidc-project1-template1/
├── src/
│   ├── app.py
│   ├── vectordb.py
│   ├── streamlit.py
|   |__ image file
├── data/
│   ├── Kepler College_Student Handbook.txt
├── .env
├── requirements.txt
├── README.md



1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/<your-project-name>.git
   cd <your-project-name>


pip install -r requirements.txt

## Then set the environment variables 
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=llama3-8b-8192
CHROMA_COLLECTION_NAME=my_collection




To run this app, 
streamlit run src/streamlit_app.py

To test this app ,
you can use this prompt , "what the publication is all about"

## Author
HARERIMANA Honore
Business Analyst and Machine learning engineer
