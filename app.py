import streamlit as st
import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from langchain.vectorstores import Pinecone
import hmac


# Authentication:
def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)



    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            
            # Don't store the username or password
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False


    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("Username or password incorrect")
    return False

# Do not continue until authenticated
if not check_password():
    st.stop()



# Initialize Pinecone
PINECONE_API_KEY = st.secrets['PINECONE_API_KEY']
PINECONE_API_ENV = "gcp-starter"
index_name = "mti"

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_API_ENV)

# Initilize OpenAI
OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)


# Get text from PDF
def get_pdf_text(pdf_docs):
    text = ""
    pdf_reader = PdfReader(pdf_docs)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Split text into chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
    )
    chunks = text_splitter.split_text(text)
    return chunks

# Upload chunks to Pinecone
def get_vectorstore(text_chunks, pdf_name):
    text = [f'{pdf_name}: {chunk}' for chunk in text_chunks]
    meta = [{'filename' : pdf_name} for _ in range(len(text_chunks))]
    vectorstore = Pinecone.from_texts(text, embeddings, index_name=index_name, metadatas=meta)
    return vectorstore



# Wepage
def main():
    st.set_page_config(page_title="Upload Files", page_icon=":outbox_tray:")
    st.header("Upload Files :outbox_tray:")
    # st.subheader("Your documents")
    
    with st.form('Uploader', clear_on_submit=True):
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'",
            accept_multiple_files=True,
            type='pdf'
        )
    
        if st.form_submit_button("Process"):
            with st.spinner("Processing"):
                for pdf in pdf_docs:
                    # get pdf text
                    raw_text = get_pdf_text(pdf)
        
                    # get the text chunks
                    text_chunks = get_text_chunks(raw_text)
        
                    # create vector store
                    vectorstore = get_vectorstore(text_chunks, pdf.name)
    
            st.write('Upload complete.')
    

if __name__ == '__main__':
    main()
