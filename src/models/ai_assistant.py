import os
import platform
import sys
import time
import openai
from colorama import init
from colorama import Fore, Back, Style
import time
import json
from datetime import datetime


initial_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")


def add_message(message, initialtime, session_id):
    now = datetime.now()
    time_str = now.strftime("%H-%M-%S")
    date_str = now.strftime("%Y-%m-%d")
    session_dir = os.path.join("data", "conversations", f"session_{session_id}")
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)

    filepath = os.path.join(session_dir, f"{initialtime}.txt")

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{time_str}: {message.strip()}\n")


def find_gguf_file():
    """
    Find a single .gguf file in the specified directory.

    Parameters:
    model_dir (str): The directory to search for .gguf files.

    Returns:
    str: The path to the .gguf file if exactly one is found.

    Raises:
    FileNotFoundError: If no .gguf files are found.
    ValueError: If more than one .gguf file is found.
    """
    MODEL_DIR = "src/models/model"

    # List all files in the specified directory
    files = os.listdir(MODEL_DIR)
    # Filter for .gguf files
    gguf_files = [file for file in files if file.endswith('.gguf')]

    if len(gguf_files) == 0:
        raise FileNotFoundError(f"No .gguf files found in directory: {MODEL_DIR}")
    elif len(gguf_files) > 1:
        raise ValueError(
            f"Multiple .gguf files found in directory: {MODEL_DIR}. Please ensure there is only one .gguf file.")

    # Return the single .gguf file found
    return os.path.join(MODEL_DIR, gguf_files[0])


def initialize_client():
    client = openai.OpenAI(base_url="http://localhost:8004/v1/", api_key="not-needed")
    return client


def process_chat_completions(client, history):
    response = client.chat.completions.create(
        model="local-model",
        messages=history,
        temperature=0.7,
        stream=True,
        max_tokens=150
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            char = chunk.choices[0].delta.content
            print(char, end="", flush=True)
            time.sleep(0.05)  # Add a small delay to simulate typing effect

    return response


def chat_loop(prompt, client, model_path, system_prompt="You are an intelligent assistant. You always flawlessly provide straight to the point well-reasoned answers that are both correct and helpful."):
    history = [
        {"role": "system",
         "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    #  print(Fore.LIGHTMAGENTA_EX + prompt, end="\n")
    response = client.chat.completions.create(
        model=model_path,
        messages=history,
        stream=True,
        max_tokens=4096,
    )
    answer = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            answer += chunk.choices[0].delta.content
            print(
                chunk.choices[0].delta.content,
                end="",
                flush=True,
            )
    print()
    print()
    print("> ")

    print("THIS IS THE ANSWER:::\n\n{{{", answer, "}}}\n\n")
    add_message(answer, initial_time, session_id="fake_session_id")


def load_agent_from_json(agent_name):
    with open("data/agents.json", "r") as file:
        agents = json.load(file)

    for agent in agents:
        if agent["name"].lower() == agent_name.lower():
            return agent

    raise ValueError(f"No agent found with the name: {agent_name}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ai_assistant.py \"<user_input>\" [<agent_name>]")
        sys.exit(1)

    user_input = sys.argv[1]
    initial_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    add_message(user_input, initial_time, session_id="fake_session_id")

    if user_input == "exit" or user_input == "quit":
        exit(0)

    agent_name = sys.argv[2] if len(sys.argv) > 2 else None

    init()
    client = initialize_client()
    model_path = find_gguf_file()

    if agent_name:
        try:
            agent = load_agent_from_json(agent_name)
            system_prompt = agent["instructions"]

        except Exception as e:
            print(f"Error loading agent: {e}")
            sys.exit(1)
    else:
        system_prompt = "You are an intelligent assistant. You always flawlessly provide straight to the point well-reasoned answers that are both correct and helpful."

    chat_loop(user_input, client, model_path, system_prompt)


if __name__ == "__main__":
    main()
