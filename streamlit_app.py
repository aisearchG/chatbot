import streamlit as st
from openai import OpenAI
import traceback
import PyPDF2
import io
from PIL import Image
import pytesseract

# Show title and description
st.title("📚 AI Study Buddy")
st.write("Your personal AI assistant for studying and learning.")

# Set up session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "subject" not in st.session_state:
    st.session_state.subject = None

if "uploaded_file_content" not in st.session_state:
    st.session_state.uploaded_file_content = None

# Subject selection
subjects = ["Mathematics", "Science", "History", "Literature", "Computer Science"]
selected_subject = st.selectbox("Select a subject:", subjects)

if selected_subject != st.session_state.subject:
    st.session_state.subject = selected_subject
    st.session_state.messages = []  # Clear chat history when subject changes

# File uploader
uploaded_file = st.file_uploader("Upload a PDF or image file containing problems", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            st.session_state.uploaded_file_content = text_content
            st.success("PDF file uploaded and processed successfully!")
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
    else:
        try:
            image = Image.open(uploaded_file)
            text_content = pytesseract.image_to_string(image)
            st.session_state.uploaded_file_content = text_content
            st.success("Image file uploaded and processed successfully!")
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")

# Display uploaded file content
if st.session_state.uploaded_file_content:
    with st.expander("View uploaded content"):
        st.text(st.session_state.uploaded_file_content)

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
    resources for further learning when possible. If the student has uploaded a file, refer to its 
    content when answering questions about specific problems or topics from the file."""

    # Display existing chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input(f"Ask a question about {st.session_state.subject} or the uploaded content..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        try:
            full_messages = [{"role": "system", "content": system_message}]
            if st.session_state.uploaded_file_content:
                full_messages.append({"role": "system", "content": f"Uploaded file content: {st.session_state.uploaded_file_content}"})
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

# Add a button to clear the chat history and uploaded content
if st.button("Clear Chat History and Uploaded Content"):
    st.session_state.messages = []
    st.session_state.uploaded_file_content = None
    st.experimental_rerun()