from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.llms.llamacpp import LlamaCpp

# from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer, util
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from dotenv import load_dotenv
import streamlit as st

# Set the page configuration first
st.set_page_config(page_title="Chat with your PDFs", page_icon=":books:")

css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px; 
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://i.ibb.co/rdZC7LZ/Photo-logo-1.png">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''

def prepare_docs(pdf_docs):
    docs = []
    metadata = []
    content = []

    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for index, text in enumerate(pdf_reader.pages):
            doc_page = {'title': f"{pdf.name} page {index + 1}",
                        'content': pdf_reader.pages[index].extract_text()}
            docs.append(doc_page)
    for doc in docs:
        content.append(doc["content"])
        metadata.append({
            "title": doc["title"]
        })
    print("Content and metadata are extracted from the documents")
    return content, metadata


def get_text_chunks(content, metadata):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=512,
        chunk_overlap=256,
    )
    split_docs = text_splitter.create_documents(content, metadatas=metadata)
    print(f"Documents are split into {len(split_docs)} passages")
    return split_docs


def ingest_into_vectordb(split_docs):
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})
    db = FAISS.from_documents(split_docs, embeddings)

    DB_FAISS_PATH = 'vectorstore/db_faiss'
    db.save_local(DB_FAISS_PATH)
    return db


def get_conversation_chain(vectordb):
    llama_llm = LlamaCpp(
        model_path="src/models/model/tinyllama-1.1b-1t-openorca.Q5_K_M.gguf",
        temperature=0.75,
        max_tokens=200,
        top_p=1,
        n_ctx=3000,
        verbose=False)

    retriever = vectordb.as_retriever()

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True, output_key='answer')

    conversation_chain = (ConversationalRetrievalChain.from_llm
        (
        llm=llama_llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True
    )
    )
    print("Conversational Chain created for the LLM using the vector store")
    return conversation_chain


def validate_answer_against_sources(response_answer, source_documents):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    similarity_threshold = 0.5
    source_texts = [doc.page_content for doc in source_documents]
    answer_embedding = model.encode(response_answer, convert_to_tensor=True)
    source_embeddings = model.encode(source_texts, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(answer_embedding, source_embeddings)
    if any(score.item() > similarity_threshold for score in cosine_scores[0]):
        return True

    return False


def handle_userinput(user_question):
    if st.session_state.conversation is None:
        st.error("Please upload and process documents before asking questions.")
        return

    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


if __name__ == '__main__':
    st.write(css, unsafe_allow_html=True)
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.header("Chat with multiple PDFs :books:")

    user_question = st.text_input("Ask a question about your documents:")
    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True, type=["pdf"])
        if st.button("Process"):
            if pdf_docs is not None:
                with st.spinner("Processing"):
                    content, metadata = prepare_docs(pdf_docs)
                    split_docs = get_text_chunks(content, metadata)
                    vectorstore = ingest_into_vectordb(split_docs)
                    st.session_state.conversation = get_conversation_chain(vectorstore)
                    st.success("Documents processed successfully!")
            else:
                st.error("Please upload at least one PDF document.")
