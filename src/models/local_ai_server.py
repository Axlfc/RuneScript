import sys
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, HTTPException
import copy
import uvicorn
from langchain_core.messages import HumanMessage

from pydantic import BaseModel

from langchain_community.llms import CTransformers  # Updated import
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from handlers import MyCustomHandler
from queue import Queue
import asyncio
from threading import Thread


# Enable verbose to debug the LLM's operation
verbose = False

# Constants
MODEL_PATH = "model/tinyllama-1.1b-1t-openorca.Q4_K_M.gguf"

# Initialize the callback managers
callback_manager = AsyncCallbackManager([AsyncCallbackHandler()])
callbacks = AsyncCallbackManager([StreamingStdOutCallbackHandler()])

# Model configuration
config = {'max_new_tokens': 256, 'repetition_penalty': 1.5, 'temperature': 0.42, 'top_k': 50}


# Create FastAPI app
app = FastAPI(
    title="Inference API for TinyLlamaOO",
    description="A simple API that uses TinyLlama OpenOrca as a chatbot",
    version="1.0",
)

streamer_queue = Queue()
my_handler = MyCustomHandler(streamer_queue)


# Initialize the model
llm = CTransformers(model=MODEL_PATH, config=config, model_type='llama',
                    callbacks_manager=callback_manager, verbose=False,
                    callbacks=callbacks)

# llm = ChatOpenAI(streaming=True, callbacks=[my_handler], temperature=0.7)


def generate(query):
    llm.invoke([HumanMessage(content=query)])


def start_generation(query):
    thread = Thread(target=generate, kwargs={"query": query})
    thread.start()


async def response_generator(query):
    start_generation(query)
    while True:
        value = streamer_queue.get()
        if value is None:
            break
        yield value
        streamer_queue.task_done()
        await asyncio.sleep(0.1)


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
async def stream(query: str):
    print(f'Query received: {query}')
    return StreamingResponse(response_generator(query), media_type='text/event-stream')


def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8004)


def test_app_server():
    while True:
        question = input("Ask me a question: ")
        if question == "stop":
            sys.exit(1)
        output = llm.invoke(
            question,
            max_tokens=512,
            stop=["Q:", "\n"],
            echo=True
        )
        print(f"\n{output}")


# Pydantic models for request and response
class Message(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    n: int = 1


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


@app.post('/v1/chat/completions')
async def chat_completions(request: CompletionRequest):
    try:
        messages = request.messages
        prompt = '\n'.join([f"{msg.role}\n{msg.content}" for msg in messages])
        res = llm.invoke(prompt, max_tokens=request.max_tokens, temperature=request.temperature, repeat_penalty=1.5)

        if 'choices' in res and len(res['choices']) > 0 and 'text' in res['choices'][0]:
            async def generate():
                for line in res['choices'][0]['text'].split('\n'):
                    yield line + "\n"
                yield ""

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            print("Unexpected response format:", res)
            raise HTTPException(status_code=500, detail=f"Invalid response from model:\n{res}")

    except Exception as e:
        print("ERROR in chat_completions endpoint:\t", e)
        raise HTTPException(status_code=500, detail=f"Internal server error occurred. {e}")


if __name__ == "__main__":
    start_server()
    # test_app_server()
