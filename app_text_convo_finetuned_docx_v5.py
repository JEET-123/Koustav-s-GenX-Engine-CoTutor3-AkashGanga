import streamlit as st
import openai
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import pandas as pd
import base64
from docx import Document
import io
import os
import time

openai.api_type = "azure"

# Set page configuration
st.set_page_config(page_title="Koustav's GenX Engine - CoTutor3(AkashGanga)", page_icon='👽', layout="wide")

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('AZURE_OPENAI_API_KEY')

openai.api_base = "https://kiit-ai-instance-01.openai.azure.com/"
openai.api_version = "2023-09-15-preview"

# Custom CSS for styling
def add_custom_css():
    st.markdown("""
        <style>
        .stApp {
            background: url('https://wallpaperaccess.com/full/4379622.jpg');
            background-size: cover;
            color: #ffffff;
        }

        header {
            background: rgba(20, 20, 20, 0.6);
            padding: 10px;
            border-radius: 10px;
            color: white;
        }

        .sidebar .sidebar-content {
            background: rgba(30, 30, 30, 0.4);
            color: #ffffff;
        }

        .stTextInput > div > div > input {
            background: rgba(30, 30, 30, 0.6);
            color: #ffffff;
            border-radius: 10px;
        }

        .stButton > button {
            background: #0078D4;
            color: #ffffff;
            border: None;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            transition: background 0.3s;
        }

        .stButton > button:hover {
            background: #005a9e;
        }

        .stSelectbox > div > div {
            background: rgba(30, 30, 30, 0.4);
            color: #ffffff;
            border-radius: 10px;
        }

        .stContainer {
            background: rgba(30, 30, 30, 0.4);
            border-radius: 10px;
            padding: 20px;
        }

        a.download-link {
            color: #ffcc00;
            text-decoration: None;
        }

        a.download-link:hover {
            text-decoration: underline;
        }

        h1, h2, h3, h4, h5, h6 {
            color: white;
        }

        .subheading {
            color: white;
        }
        
        .answer-text {
            color: black !important;
        }

        .info-message {
            color: #ffcc00;
        }
        </style>
        """, unsafe_allow_html=True)

# Function to return the response with retry logic
def load_answer(question, conversation_history, pdf_text):
    context = pdf_text + "\n" + "\n".join(conversation_history) + f"\nUser: {question}\nAI:"
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            chat = AzureChatOpenAI(
                model_name="gpt-35-turbo",
                deployment_name="kiit-gpt35-turbo",
                api_version="2023-09-15-preview"
            )
            response = chat.invoke(
                input=context,
                max_tokens=150  # Adjust as per your requirement
            )
            return response.content
        except openai.OpenAIError as e:  # Correct exception handling
            if "Rate limit" in str(e) or "Please reduce your request rate" in str(e):
                st.warning(f"Rate limit error. Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                st.error(f"An error occurred: {e}")
                break
        except Exception as e:  # Catch any other exception
            st.error(f"An unexpected error occurred: {e}")
            break
    return "Failed to get a response after several attempts."

# Function to clear conversation history
def clear_history():
    st.session_state.conversation_history = []

# Function to download conversation history as text file
def download_history_text():
    history_str = "\n".join(st.session_state.conversation_history)
    b64 = base64.b64encode(history_str.encode()).decode()
    href = f'<a class="download-link" href="data:text/plain;base64,{b64}" download="conversation_history.txt">Download conversation history (TXT)</a>'
    st.markdown(href, unsafe_allow_html=True)

# Function to download conversation history as CSV file
def download_history_csv():
    history_df = pd.DataFrame(st.session_state.conversation_history, columns=["Conversation"])
    csv = history_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a class="download-link" href="data:file/csv;base64,{b64}" download="conversation_history.csv">Download conversation history (CSV)</a>'
    st.markdown(href, unsafe_allow_html=True)

# Function to extract text from DOCX file
def extract_text_from_docx(file_path):
    doc = Document(file_path)
    content = ""
    for para in doc.paragraphs:
        content += para.text + "\n"
    return content

# Initialize the session state to store the conversation history and DOCX text
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'docx_text' not in st.session_state:
    docx_text = extract_text_from_docx(r"C:\Users\kousdutta\Desktop\Project_X\AzureOpenAI\Mid_Sem_Project_Report.docx")
    st.session_state.docx_text = docx_text

if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

if 'response' not in st.session_state:
    st.session_state.response = ''

# Predefined questions
predefined_questions = [
    "Tell me about the core theme of the project.",
    "What is Price Elasticity Modelling",
    "What are the Marketing Mix Models being discussed here ?",
    "What is the problem, this project is solving",
    "What are the technologies used in the project"
]

# Add custom CSS for styling
add_custom_css()

# App UI starts here
st.header("CoTutor2: GenX Engine Pilot")

# Sidebar for navigation
tab = st.sidebar.selectbox("Choose a section", ["Chat", "Conversation History"], key="section")

# Chat section
if tab == "Chat":
    # Function to get text input
    def get_text():
        input_text = st.text_input("You: ", key="input", value=st.session_state.user_input, on_change=reset_predefined_question)
        return input_text

    # Function to reset predefined question
    def reset_predefined_question():
        st.session_state.predefined_question = ""

    # Initialize predefined_question in session state
    if 'predefined_question' not in st.session_state:
        st.session_state.predefined_question = ""

    user_input = get_text()
    predefined_question = st.selectbox("Or select a predefined question:", [""] + predefined_questions, key="predefined_question")
    col1, col2 = st.columns([1, 1])
    with col1:
        submit = st.button('Generate')
    with col2:
        clear = st.button('Clear History')

    # If clear history button is clicked
    if clear:
        clear_history()

    # If generate button is clicked
    if submit and (user_input or predefined_question):
        # Use the predefined question if available
        question = predefined_question if predefined_question else user_input

        # Get the previous conversation history
        conversation_history = st.session_state.conversation_history

        # Generate response based on the current question and conversation history
        response = load_answer(question, conversation_history, st.session_state.docx_text)

        # Update the conversation history
        conversation_history.append(f"User: {question}")
        conversation_history.append(f"AI: {response}")

        # Save the updated conversation history, user input, and response in session state
        st.session_state.conversation_history = conversation_history
        st.session_state.user_input = user_input
        st.session_state.response = response

    # Display the latest response
    if st.session_state.response:
        st.subheader("Answer:")
        st.write(st.session_state.response)

    # Display a message if there is no input
    if not user_input and not predefined_question and submit:
        st.error("Please enter a question or select a predefined question.")

# Conversation History section
elif tab == "Conversation History":
    st.subheader("Conversation History")
    conversation_history = st.session_state.conversation_history

    if conversation_history:
        for i in range(0, len(conversation_history), 2):
            st.text(f"{conversation_history[i]}")
            st.text(f"{conversation_history[i+1]}")
        st.markdown("---")
        download_history_text()
        download_history_csv()
    else:
        st.info("No conversation history yet.")

# Apply custom styles to specific elements
st.markdown(
    """
    <style>
    .subheading {
        color: white !important;
    .download-link {
        color: #ffcc00 !important;
    }
    .info-message {
        color: #ffcc00 !important;
    }
    </style>
    """, unsafe_allow_html=True
)
