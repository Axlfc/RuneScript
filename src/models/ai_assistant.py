import os
import sys
import time
import openai
from colorama import init
from colorama import Fore, Back, Style
import time


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
    # Point to the local server
    client = openai.OpenAI(base_url="http://localhost:8004/v1/", api_key="not-needed")
    #  client = openai.OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
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


'''def main_chat_loop(client, text_prompt):
    history = [
        {"role": "system", "content": "You are an intelligent assistant. You always flawlessly provide straight to the point well-reasoned answers that are both correct and helpful."},
        {"role": "user", "content": text_prompt},
    ]

    try:
        user_input = process_chat_completions(client, history)
        print()
        user_input = input("> ")
        if user_input.strip():
            history.append({"role": "user", "content": user_input})
    except Exception as e:
        #print(f"Error during processing: {e}")
        not_the_text = str(e)
        output = not_the_text.split("model:")[1] if "model:" in not_the_text else not_the_text

        last_brace_index = output.rfind('}')
        if last_brace_index != -1:
            output = output[:last_brace_index]

        print(output.replace("\\n", "\n\n"))
        print("THE TYPE OF THE OUTPUT IS:\t{", type(output), "}")
        #return output
'''


def chat_loop(prompt):
    #  print(Fore.LIGHTMAGENTA_EX + prompt, end="\n")
    response = client.chat.completions.create(
        model=MODEL_PATH,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        stream=True,
        max_tokens=1000,
    )
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            print(
                chunk.choices[0].delta.content,
                end="",
                flush=True,
            )
    print()
    print()
    print("> ")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ai_assistant.py <user_input>")
        sys.exit(1)

    MODEL_PATH = find_gguf_file()

    user_input = sys.argv[1]

    init()

    client = initialize_client()
    #  time.sleep(5)

    chat_loop(user_input)

    #  main_chat_loop(client, user_input)