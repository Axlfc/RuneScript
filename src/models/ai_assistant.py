import os
import platform
import sys
import time
import openai
import requests
from colorama import init
from colorama import Fore, Back, Style
import time
import json
from datetime import datetime
from dotenv import load_dotenv
# import anthropic
from src.controllers.parameters import read_config_parameter

initial_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")


def add_message(session_id, message):
    session_dir = os.path.join("data", "conversations", f"session_{session_id}")
    file_path = os.path.join(session_dir, f"{session_id}.json")
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    if not os.path.isfile(file_path):
        data = {"session_id": session_id, "messages": []}
    else:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    data["messages"].append(
        {"timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "content": message}
    )
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def find_gguf_file():
    MODEL_DIR = "src/models/model/text"
    files = os.listdir(MODEL_DIR)
    gguf_files = [file for file in files if file.endswith(".gguf")]
    if len(gguf_files) == 0:
        raise FileNotFoundError(f"No .gguf files found in directory: {MODEL_DIR}")
    elif len(gguf_files) > 1:
        raise ValueError(
            f"Multiple .gguf files found in directory: {MODEL_DIR}. Please ensure there is only one .gguf file."
        )
    return os.path.join(MODEL_DIR, gguf_files[0])


def initialize_client():
    client = openai.OpenAI(base_url="http://localhost:8004/v1/", api_key="not-needed")
    return client


def initialize_client_with_parameters(url, api_key):
    client = openai.OpenAI(base_url=url, api_key=api_key)
    return client


def process_chat_completions(client, history):
    response = client.chat.completions.create(
        model="local-model",
        messages=history,
        temperature=0.7,
        stream=True,
        max_tokens=150,
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            char = chunk.choices[0].delta.content
            print(char, end="", flush=True)
            time.sleep(0.05)
    return response


def chat_loop(
    prompt,
    client,
    model_path,
    system_prompt="You are an intelligent assistant. You always flawlessly provide straight to the point well-reasoned answers that are both correct and helpful.",
    session_id=0,
):
    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    response = client.chat.completions.create(
        model=model_path, messages=history, stream=True, max_tokens=4096
    )
    answer = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            message = chunk.choices[0].delta.content
            print(message, end="", flush=True)
            answer += message
    print("\n> ")
    print()
    print("> ")


def load_agent_from_json(agent_name):
    with open("data/agents.json", "r") as file:
        agents = json.load(file)
    for agent in agents:
        if agent["name"].lower() == agent_name.lower():
            return agent
    raise ValueError(f"No agent found with the name: {agent_name}")


def initialize_gemini_client():
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    return {
        "api_key": GEMINI_API_KEY,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
    }


def process_gemini_chat(client, prompt):
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(
            f"{client['base_url']}?key={client['api_key']}", headers=headers, json=data
        )
        response.raise_for_status()
        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate:
                content = candidate["content"]
                if "parts" in content and len(content["parts"]) > 0:
                    return content["parts"][0]["text"]
                else:
                    return "Error: No text content found in the response."
            else:
                return "Error: Unexpected response structure from Gemini API."
        else:
            return "Error: No valid response received from Gemini API."
    except requests.exceptions.RequestException as e:
        return f"Error: Request to Gemini API failed. Details: {str(e)}"
    except json.JSONDecodeError:
        return "Error: Invalid response received from Gemini API."
    except Exception as e:
        return f"Error: An unexpected error occurred. Details: {str(e)}"


def chat_loop_gemini(prompt, client, system_prompt, session_id):
    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    full_prompt = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation]
    )
    response = process_gemini_chat(client, full_prompt)
    if response.startswith("Error:"):
        print(f"An error occurred: {response}")
    else:
        print("Gemini:", response)
    print("\n> ")
    print()
    print("> ")


def initialize_claude_client():
    load_dotenv()
    CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    # return anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    print("Not supported")


def process_claude_chat(client, prompt):
    try:
        response = client.completions.create(
            model="claude-3-opus-20240229",
            max_tokens_to_sample=1000,
            temperature=0.7,
            prompt=f"""

Human: {prompt}

Assistant:""",
        )
        return response.completion
    except anthropic.APIError as e:
        return f"Error: Claude API request failed. Details: {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred. Details: {str(e)}"


def chat_loop_claude(prompt, client, system_prompt, session_id):
    full_prompt = f"{system_prompt}\n\nHuman: {prompt}\n\nAssistant:"
    response = process_claude_chat(client, full_prompt)
    if response.startswith("Error:"):
        print(f"An error occurred: {response}")
    else:
        print("Claude:", response)
    print("\n> ")
    print()
    print("> ")


def main():
    if len(sys.argv) < 2:
        print('Usage: python ai_assistant.py "<user_input>" [<agent_name>]')
        sys.exit(1)
    user_input = sys.argv[1]
    session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    if user_input == "exit" or user_input == "quit":
        exit(0)
    agent_name = sys.argv[2] if len(sys.argv) > 2 else None
    init()
    selected_llm_server_provider = read_config_parameter(
        "options.network_settings.last_selected_llm_server_provider"
    )
    server_url = read_config_parameter("options.network_settings.server_url")
    api_key = read_config_parameter("options.network_settings.api_key")
    if agent_name:
        try:
            agent = load_agent_from_json(agent_name)
            system_prompt = agent["instructions"]
        except Exception as e:
            print(f"Error loading agent: {e}")
            sys.exit(1)
    else:
        system_prompt = "You are an intelligent assistant. You always flawlessly provide straight to the point well-reasoned answers that are both correct and helpful."
    if selected_llm_server_provider == "llama-cpp-python":
        client = initialize_client_with_parameters(server_url, api_key)
        model_path = find_gguf_file()
        chat_loop(user_input, client, model_path, system_prompt, session_id)
    elif selected_llm_server_provider == "gemini":
        client = initialize_gemini_client()
        chat_loop_gemini(user_input, client, system_prompt, session_id)
    elif selected_llm_server_provider == "claude":
        client = initialize_claude_client()
        chat_loop_claude(user_input, client, system_prompt, session_id)
    else:
        print("UNSUPPORTED LLM SERVER PROVIDER")


if __name__ == "__main__":
    main()
