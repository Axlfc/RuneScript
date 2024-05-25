import sys
import time

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
    # client = openai.OpenAI(base_url="http://localhost:8004/v1/", api_key="not-needed")
    client = openai.OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    return client

def process_chat_completions(client, history):
    completion = client.chat.completions.create(
        model="local-model",
        messages=history,
        temperature=0.7,
        stream=True,
        max_tokens=150
    )

    for chunk in completion:
        if chunk.choices[0].delta.content:
            char = chunk.choices[0].delta.content
            print(char, end="", flush=True)
            time.sleep(0.05)  # Add a small delay to simulate typing effect

    return completion

def main_chat_loop(client, text_prompt):
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ai_assistant.py <user_input>")
        sys.exit(1)

    user_input = sys.argv[1]
    client = initialize_client()
    main_chat_loop(client, user_input)