import streamlit as st
from openai import OpenAI
import traceback
import PyPDF2
import io
from PIL import Image
import pytesseract

# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text_content = ""
    for page in pdf_reader.pages:
        text_content += page.extract_text()
    return text_content

# Sidebar for uploads and subject selection
with st.sidebar:
    st.header("📚 Study Setup")
    
    # Subject selection
    subjects = ["Mathematics", "Science", "History", "Literature", "Computer Science"]
    selected_subject = st.selectbox("Select a subject:", subjects)

    st.subheader("Expand Knowledge Base")
    knowledge_file = st.file_uploader("Upload a PDF file to expand the knowledge base", type=["pdf"])

    st.subheader("Upload Current Problem")
    problem_file = st.file_uploader("Upload a PDF or image file containing the current problem", type=["pdf", "png", "jpg", "jpeg"])

    # Add buttons to clear different types of data
    st.subheader("Clear Data")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.experimental_rerun()
    if st.button("Clear Current Problem"):
        st.session_state.current_problem = None
        st.experimental_rerun()
    if st.button("Clear Knowledge Base"):
        st.session_state.knowledge_base = ""
        st.experimental_rerun()

# Main area
st.title("AI Study Buddy")
st.write("Your personal AI assistant for studying and learning.")

# Set up session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "subject" not in st.session_state:
    st.session_state.subject = None
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = ""
if "current_problem" not in st.session_state:
    st.session_state.current_problem = None

# Update subject if changed
if selected_subject != st.session_state.subject:
    st.session_state.subject = selected_subject
    st.session_state.messages = []  # Clear chat history when subject changes

# Process knowledge base file
if knowledge_file is not None:
    try:
        new_knowledge = extract_text_from_pdf(knowledge_file)
        st.session_state.knowledge_base += f"\n\nNew Information:\n{new_knowledge}"
        st.sidebar.success("Knowledge base expanded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error processing PDF: {str(e)}")

# Process current problem file
if problem_file is not None:
    if problem_file.type == "application/pdf":
        try:
            st.session_state.current_problem = extract_text_from_pdf(problem_file)
            st.sidebar.success("Problem PDF uploaded and processed successfully!")
        except Exception as e:
            st.sidebar.error(f"Error processing PDF: {str(e)}")
    else:
        try:
            image = Image.open(problem_file)
            st.session_state.current_problem = pytesseract.image_to_string(image)
            st.sidebar.success("Problem image uploaded and processed successfully!")
        except Exception as e:
            st.sidebar.error(f"Error processing image: {str(e)}")

# Display current problem
if st.session_state.current_problem:
    with st.expander("View current problem"):
        st.text(st.session_state.current_problem)

# OpenAI API setup
openai_api_key = st.secrets.get("openai_api_key")
if not openai_api_key:
    st.error("Please add your OpenAI API key to the app's secrets.", icon="🔑")
else:
    client = OpenAI(api_key=openai_api_key)

    # System message to guide the AI's behavior
    system_message = f"""You are an AI study assistant specializing in {st.session_state.subject}. 
    Your role is to help students understand concepts, answer questions, and provide explanations 
    in a clear, concise manner. Use examples and analogies when appropriate to aid understanding. 
    If a question is unclear, ask for clarification. Always encourage critical thinking and provide 
    resources for further learning when possible. If the student has uploaded a problem, refer to its 
    content when answering questions. Use the expanded knowledge base to provide more accurate and 
    up-to-date information."""

    # Display existing chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input(f"Ask a question about {st.session_state.subject} or the uploaded problem..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        try:
            full_messages = [{"role": "system", "content": system_message}]
            if st.session_state.knowledge_base:
                full_messages.append({"role": "system", "content": f"Additional knowledge: {st.session_state.knowledge_base}"})
            if st.session_state.current_problem:
                full_messages.append({"role": "system", "content": f"Current problem: {st.session_state.current_problem}"})
            full_messages.extend(st.session_state.messages)

            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=full_messages,
                stream=True,
            )

            with st.chat_message("assistant"):
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error(traceback.format_exc())