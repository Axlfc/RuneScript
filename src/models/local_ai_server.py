import sys
from fastapi import FastAPI, Request
import asyncio
from langchain_community.llms import CTransformers  # Updated import
import copy
import uvicorn

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


# Enable verbose to debug the LLM's operation
verbose = False

# Constants
MODEL_PATH = "model/tinyllama-1.1b-1t-openorca.Q5_K_M.gguf"

# Initialize the callback managers
callback_manager = AsyncCallbackManager([AsyncCallbackHandler()])
callbacks = AsyncCallbackManager([StreamingStdOutCallbackHandler()])

# Model configuration
config = {'max_new_tokens': 256, 'repetition_penalty': 1.1, 'temperature': 0.7, 'top_k': 50}

# Initialize the model
llm = CTransformers(model=MODEL_PATH, config=config, model_type='llama',
                    callbacks_manager=callback_manager, verbose=True,
                    callbacks=callbacks)

'''question = "who is the president of the united states?"

from langchain import PromptTemplate, LLMChain

template = """User: {question}

Assistant:"""

prompt = PromptTemplate(template=template, input_variables=["question"])

llm_chain = LLMChain(prompt=prompt, llm=llm)

response = llm_chain.run(question=question)'''

prompt = '''
### User:
Write a script for a episode of "Sherlock Holmes" with episode name "The Man in the High Castle".

### Response:
'''


# Create FastAPI app
app = FastAPI(
    title="Inference API for TinyLlamaOO",
    description="A simple API that uses TinyLlama OpenOrca as a chatbot",
    version="1.0",
)


@app.get('/')
async def hello():
    return {"hello": "Artificial Intelligence enthusiast"}


@app.get('/model')
async def model():
    text = "Who is Tony Stark?"
    template = f"""system\nYou are a helpful ChatBot assistant.\nuser\n{text}\nassistant"""
    res = llm(template)
    result = copy.deepcopy(res)
    return {"result": result['choices'][0]['text']}


@app.get('/tinyllama')
async def tinyllama(text: str):
    template = f"""system\nYou are a helpful ChatBot assistant.\nuser\n{text}\nassistant"""
    res = llm(template, temperature=0.42, repeat_penalty=1.5, max_tokens=300)
    result = copy.deepcopy(res)
    return {"result": result['choices'][0]['text']}


def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)


def test_app_server():
    while True:
        question = input("Ask me a question: ")
        if question == "stop":
            sys.exit(1)
        output = llm(
            question,
            max_tokens=4096,
            temperature=0.2,
            # Nucleus sampling (mass probability index)
            # Controls the cumulative probability of the generated tokens
            # The higher top_p the more diversity in the output
            top_p=0.1
        )
        print(f"\n{output}")


if __name__ == "__main__":
    start_server()
    # test_app_server()
