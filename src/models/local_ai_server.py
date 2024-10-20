import sys
import copy
import time
import asyncio
from queue import Queue
from threading import Thread
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel
import uvicorn
from langchain_community.llms import CTransformers, LlamaCpp
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from handlers import MyCustomHandler
from langchain.schema import AIMessage, HumanMessage
from langchain.retrievers import ElasticSearchBM25Retriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from uuid import uuid4
from langchain_community.document_loaders import PyPDFLoader

MODEL_PATH = "model/text/llama-2-7b-chat.Q4_K_M.gguf"
MAX_TOKENS = 8192
callback_manager = AsyncCallbackManager([AsyncCallbackHandler()])
callbacks = AsyncCallbackManager([StreamingStdOutCallbackHandler()])
config = {
    "max_new_tokens": 8192,
    "repetition_penalty": 1.5,
    "temperature": 0.42,
    "top_k": 50,
}
llm = LlamaCpp(
    model_path=MODEL_PATH,
    temperature=0.21,
    max_tokens=MAX_TOKENS,
    top_p=1,
    n_ctx=3000,
    streaming=True,
    verbose=False,
    callback_manager=callback_manager,
)
retriever = ElasticSearchBM25Retriever(index_name="your_index_name")
app = FastAPI(
    title="Inference API for TinyLlamaOO",
    description="A simple API that uses TinyLlama OpenOrca as a chatbot",
    version="1.0",
)
streamer_queue = Queue()
my_handler = MyCustomHandler(streamer_queue)


class Message(BaseModel):
    """
    Message

    Description of the class.
    """

    role: str
    content: str


class CompletionRequest(BaseModel):
    """
    CompletionRequest

    Description of the class.
    """

    messages: list[Message]
    max_tokens: int
    temperature: float


class CompletionResponseChoice(BaseModel):
    """
    CompletionResponseChoice

    Description of the class.
    """

    message: dict
    finish_reason: str


class CompletionResponse(BaseModel):
    """
    CompletionResponse

    Description of the class.
    """

    id: str
    object: str
    created: int
    model: str
    choices: list[CompletionResponseChoice]
    usage: dict


sessions = {}


async def generate(query):
    llm.stream([HumanMessage(content=query)])


async def response_generator(query, session_id):
    global sessions, llm, retriever
    if session_id not in sessions:
        sessions[session_id] = {
            "history": ConversationBufferMemory(),
            "chain": ConversationalRetrievalChain.from_llm(
                llm, retriever, memory=ConversationBufferMemory()
            ),
        }
    chain = sessions[session_id]["chain"]
    try:
        result = await chain.ainvoke(
            {"question": query, "chat_history": sessions[session_id]["history"].buffer}
        )
        for response_text in result["outputs"]:
            yield f"data: {response_text}\n\n"
    except asyncio.CancelledError:
        print(
            f"Client disconnected during response generation for session {session_id}"
        )
        return
    except ValueError as e:
        print(f"ValueError: {e}")
        return


@app.get("/")
def hello():
    """
    hello

    Args:
        None

    Returns:
        None: Description of return value.
    """
    return {"hello": "Artificial Intelligence enthusiast"}


@app.get("/model")
def model():
    """
    model

    Args:
        None

    Returns:
        None: Description of return value.
    """
    text = "Who is Tony Stark?"
    template = f"system\nYou are a helpful ChatBot assistant.\nuser\n{text}\nassistant"
    res = llm.invoke(template)
    result = copy.deepcopy(res)
    return {"result": result["choices"][0]["text"]}


@app.get("/tinyllama")
def tinyllama(text: str):
    """
    tinyllama

    Args:
        text (Any): Description of text.

    Returns:
        None: Description of return value.
    """
    template = f"system\nYou are a helpful ChatBot assistant.\nuser\n{text}\nassistant"
    res = llm.invoke(template, temperature=0.42, repeat_penalty=1.5, max_tokens=300)
    result = copy.deepcopy(res)
    return {"result": result["choices"][0]["text"]}


@app.get("/query-stream/")
async def stream(query: str, session_id: str = "default"):
    print(f"Query received: {query}")
    return StreamingResponse(
        response_generator(query, session_id), media_type="text/event-stream"
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: CompletionRequest, session_id: str = "default"):
    try:
        messages = request.messages
        prompt = "\n".join([f"{msg.role}\n{msg.content}" for msg in messages])
        res = llm.invoke(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            repeat_penalty=1.5,
        )
        response = CompletionResponse(
            id=session_id,
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                {
                    "message": {
                        "role": "assistant",
                        "content": res["choices"][0]["text"],
                    },
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(res["choices"][0]["text"].split()),
                "total_tokens": len(prompt.split())
                + len(res["choices"][0]["text"].split()),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid response from model:\n{res}\nEXCEPTION:\n{e}",
        )


def start_server():
    """
    start_server

    Args:
        None

    Returns:
        None: Description of return value.
    """
    uvicorn.run(app, host="0.0.0.0", port=8004)


if __name__ == "__main__":
    start_server()
