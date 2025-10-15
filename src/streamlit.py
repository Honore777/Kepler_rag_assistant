import streamlit as st
from app import answer_question  
import base64
import os

# Page configuration
st.set_page_config(
    page_title="Kepler College Handbook Assistant",
    page_icon="🤖",
    layout="wide"
)

st.image("success_week.jpg", use_container_width=True)

st.markdown(
    "<h1 style='text-align: center; background-color:green; color:white; padding:10px; border-radius:10px;'>"
    "Kepler College Handbook RAG Assistant"
    "</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    Ask any question about the Kepler College Student Handbook.  
    The AI will only answer based on the handbook content.
    """
)


user_query = st.text_input("Enter your question here:")


if st.button("Get Answer") and user_query.strip() != "":
    with st.spinner("Generating answer..."):

              response_content = answer_question(user_query)
              st.subheader("Answer:")

  
    st.markdown(
        f"""
        <div style="
            background-color: #f7f7f7;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            color: #000;
            font-size: 16px;
            line-height: 1.6;
            margin-top: 10px;
        ">
            {response_content}
        </div>
        """,
        unsafe_allow_html=True
    )


        
          