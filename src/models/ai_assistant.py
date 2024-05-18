import sys


try:
    from pathlib import Path

    current_script_path = Path(__file__).parent

    content_path = current_script_path.joinpath('../../../../../UE5-python').resolve()

    sys.path.append(str(content_path))
    from Content.Python_dependencies.latest_openai import openai
except Exception as es:
    import openai


def initialize_client():
    # Point to the local server
    # TODO: Load base_url and api_key from settings
    #  TODO: test local_ai_server.py API endpoints
    client = openai.OpenAI(base_url="http://localhost:8004/v1", api_key="not-needed")
    #client = openai.OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
    return client

def process_chat_completions(client, history):
    completion = client.chat.completions.create(
        model="local-model",  # this field is currently unused
        messages=history,
        temperature=0.7,
        stream=True,
    )

    new_message = {"role": "assistant", "content": ""}
    for chunk in completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
            new_message["content"] += chunk.choices[0].delta.content

    return new_message


def main_chat_loop(client, text_prompt):
    history = [
        {"role": "system", "content": "You are an intelligent assistant. You always flawlessly provide straight to the point well-reasoned answers that are both correct and helpful."},
        {"role": "user", "content": text_prompt},
    ]

    new_message = process_chat_completions(client, history)
    history.append(new_message)

    # Uncomment to see chat history
    # import json
    # gray_color = "\033[90m"
    # reset_color = "\033[0m"
    # print(f"{gray_color}\n{'-'*20} History dump {'-'*20}\n")
    # print(json.dumps(history, indent=2))
    # print(f"\n{'-'*55}\n{reset_color}")

    print()
    user_input = input("> ")
    if user_input.strip():
        history.append({"role": "user", "content": user_input})


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ai_assistant.py <user_input>")
        sys.exit(1)

    user_input = sys.argv[1]
    client = initialize_client()
    main_chat_loop(client, sys.argv[1])