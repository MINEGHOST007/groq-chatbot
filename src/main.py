import io
from dotenv import load_dotenv
import streamlit as st
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters.character import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

load_dotenv()

def load_document(file):
    """Load document directly from an in-memory file."""
    loader = UnstructuredPDFLoader(io.BytesIO(file.read()))
    documenta = loader.load()
    return documenta

def setup_vectorstore(documents):
    """Set up FAISS vector store."""
    embeddings = HuggingFaceEmbeddings()
    text_splitter = CharacterTextSplitter(
        is_separator_regex=False,
        separator='/n',
        chunk_size=1000,
        chunk_overlap=200
    )
    doc_chunks = text_splitter.split_documents(documents)
    vectorstore = FAISS.from_documents(doc_chunks, embeddings)
    return vectorstore

def create_chain(vectorstore):
    """Create a conversational retrieval chain with memory."""
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0
    )
    retriever = vectorstore.as_retriever()
    memory = ConversationBufferMemory(
        llm=llm,
        output_key="answer",
        memory_key="chat_history",
        return_messages=True
    )
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        chain_type="map_reduce",
        verbose=True
    )
    return chain

st.set_page_config(
    page_title="MEG-AI",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 MEG_AI - A simpler version of open source kotaemon")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

uploaded_file = st.file_uploader(label="Upload your PDF file", type=["pdf"])

if uploaded_file:
    documenta = load_document(uploaded_file)
    
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = setup_vectorstore(documenta)

    if "conversation_chain" not in st.session_state:
        st.session_state.conversation_chain = create_chain(st.session_state.vectorstore)

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask MEG....")

if user_input:
    st.session_state.chat_history.append({"role": "user", 'content': user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response = st.session_state.conversation_chain({"question": user_input})
        st.markdown(response["answer"])
        st.session_state.chat_history.append({"role": "assistant", 'content': response["answer"]})
