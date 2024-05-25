import glob
import os
import sys
import PyPDF2
import copy
import asyncio
from queue import Queue
from threading import Thread
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
import uvicorn

from langchain_community.llms import CTransformers, LlamaCpp  # Ensure correct imports
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from handlers import MyCustomHandler
from langchain.schema import AIMessage, HumanMessage
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

# Constants
MODEL_PATH = "model/llama-2-7b-chat.Q4_K_M.gguf"
DB_FAISS_PATH = 'vectorstore/db_faiss'
MAX_TOKENS = 8192

# Initialize the callback managers
callback_manager = AsyncCallbackManager([AsyncCallbackHandler()])
callbacks = AsyncCallbackManager([StreamingStdOutCallbackHandler()])

# Model configuration
config = {'max_new_tokens': 8192, 'repetition_penalty': 1.5, 'temperature': 0.42, 'top_k': 50}

# --- RAG Setup ---
def prepare_docs(pdf_docs):
    """Prepare documents and their metadata from a list of PDF file paths."""
    docs = []
    for pdf_path in pdf_docs:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        for i, page in enumerate(pages):
            docs.append({
                "title": f"{os.path.basename(pdf_path)} Page {i+1}",
                "content": page.page_content
            })
    return docs

def create_or_load_index(pdf_docs):
    """Create or load the FAISS index."""
    if os.path.exists(DB_FAISS_PATH):
        print("Loading existing FAISS index...")
        db = FAISS.load_local(DB_FAISS_PATH, HuggingFaceEmbeddings())
    else:
        print("Creating new FAISS index...")
        docs = prepare_docs(pdf_docs)
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=512, chunk_overlap=256)
        split_docs = text_splitter.create_documents([d["content"] for d in docs], metadatas=[{"title": d["title"]} for d in docs])
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})
        db = FAISS.from_documents(split_docs, embeddings)
        db.save_local(DB_FAISS_PATH)
    return db


# --- Load or create the FAISS index ---
pdf_docs = [glob.glob("../../data/pdf_docs/*.pdf")]
db = create_or_load_index(pdf_docs)
retriever = db.as_retriever()

# --- Session Management (Modified) ---
sessions = {}

# Initialize the model
llm = LlamaCpp(
    model_path=MODEL_PATH,
    temperature=0.21,
    max_tokens=MAX_TOKENS,
    top_p=1,
    n_ctx=3000,
    streaming=True,
    verbose=False
)

# Create FastAPI app
app = FastAPI(
    title="Inference API for TinyLlamaOO",
    description="A simple API that uses TinyLlama OpenOrca as a chatbot",
    version="1.0",
)

# Queue for streaming responses
streamer_queue = Queue()
my_handler = MyCustomHandler(streamer_queue)

# Pydantic models for request and response
class Message(BaseModel):
    role: str
    content: str

class CompletionRequest(BaseModel):
    messages: list[Message]
    max_tokens: int
    temperature: float

class CompletionResponseChoice(BaseModel):
    message: dict
    finish_reason: str

class CompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[CompletionResponseChoice]
    usage: dict

# Session Management (Example using a simple dictionary)
sessions = {}

# Function to generate responses
async def response_generator(query, session_id):
    global sessions, llm, retriever

    if session_id not in sessions:
        sessions[session_id] = {
            "history": ConversationBufferMemory(),
            "chain": ConversationalRetrievalChain.from_llm(
                llm, retriever, memory=sessions[session_id]["history"]
            )
        }

    chain = sessions[session_id]["chain"]
    response_text = chain.run(query)
    yield response_text

@app.get('/')
def hello():
    return {"hello": "Artificial Intelligence enthusiast"}

@app.get('/model')
def model():
    text = "Who is Tony Stark?"
    template = f"""system\nYou are a helpful ChatBot assistant.\nuser\n{text}\nassistant"""
    res = llm.invoke(template)
    result = copy.deepcopy(res)
    return {"result": result['choices'][0]['text']}

@app.get('/tinyllama')
def tinyllama(text: str):
    template = f"""system\nYou are a helpful ChatBot assistant.\nuser\n{text}\nassistant"""
    res = llm.invoke(template, temperature=0.42, repeat_penalty=1.5, max_tokens=300)
    result = copy.deepcopy(res)
    return {"result": result['choices'][0]['text']}

@app.get('/query-stream/')
async def stream(query: str, session_id: str = "default"):
    print(f'Query received: {query}')
    return StreamingResponse(response_generator(query, session_id), media_type='text/event-stream')

@app.post('/v1/chat/completions')
async def chat_completions(request: CompletionRequest, session_id: str = "default"):
    try:
        messages = request.messages
        prompt = '\n'.join([f"{msg.role}\n{msg.content}" for msg in messages])
        res = llm.invoke(prompt, max_tokens=request.max_tokens, temperature=request.temperature, repeat_penalty=1.5)

        if 'choices' in res and len(res['choices']) > 0 and 'text' in res['choices'][0]:
            result = res['choices'][0]['text']
            return {"result": result['choices'][0]['text']}
        else:
            print("Unexpected response format:", res)
            raise HTTPException(status_code=500, detail=f"Invalid response from model:\n{res}")

    except Exception as e:
        print("ERROR in chat_completions endpoint:\t", e)
        raise HTTPException(status_code=500, detail=f"Internal server error occurred. {e}")

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8004)

if __name__ == "__main__":
    start_server()
