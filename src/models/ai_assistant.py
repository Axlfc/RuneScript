import importlib
import logging
import os
import platform
import sys
import time
import requests
from colorama import init
from colorama import Fore, Back, Style
import time
import json
import io
import contextlib
from datetime import datetime
from google import genai
from google.genai.types import GenerateContentConfig, Part, SafetySetting

from dotenv import load_dotenv
import anthropic

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.controllers.parameters import read_config_parameter

# AÃ±ade tu .venv/Lib/site-packages al path si no estÃ¡ ya
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
for suffix in (('.venv', 'Lib', 'site-packages'), ('venv', 'Lib', 'site-packages')):
    path = os.path.join(base_dir, *suffix)
    if os.path.isdir(path):
        sys.path.insert(0, path)
        break

# Lista de librerÃ­as a validar
venv_libs = ["openai", "requests"]

for lib in venv_libs:
    try:
        importlib.import_module(lib)
    except ImportError as e:
        raise ImportError(
            f"No se pudo cargar la librerÃ­a '{lib}'. "
            f"AsegÃºrate de haber ejecutado `pip install {lib}` dentro de tu venv."
        ) from e

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
        max_tokens=150)
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
    session_id=0):
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


def initialize_gemini30_client():
    """Initializes the Gemini 3.0 client using the API key from environment variables."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)


def process_gemini30_chat(messages: list):
    """Processes a chat request for Gemini 3.0 with a list of messages."""
    try:
        client = initialize_gemini30_client()

        # Map standard message format to Gemini SDK format
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            # Gemini roles are 'user' and 'model'
            if role == "assistant":
                role = "model"
            elif role == "system":
                # System messages are often handled separately in Gemini
                role = "user"

            content = msg.get("content", "")
            gemini_messages.append({
                "role": role,
                "parts": [{"text": content}]
            })

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=gemini_messages
        )
        return response.text
    except Exception as e:
        return f"Error while communicating with Gemini 3.0: {str(e)}"


def chat_loop_gemini30(prompt, client, system_prompt, session_id):
    """Interactive chat loop for Gemini 3.0."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    response = process_gemini30_chat(messages)
    if response.startswith("Error:"):
        print(f"An error occurred: {response}")
    else:
        print(response)


def initialize_gemini15_client():
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    return {
        "api_key": GEMINI_API_KEY,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
    }


def initialize_gemini20_client():
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=GEMINI_API_KEY)


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


def process_gemini20_chat(client, prompt, system_prompt=None, temperature=0.7, max_tokens=300):
    try:
        # Configure the system instructions
        config = GenerateContentConfig(
            system_instruction=system_prompt or "You are a helpful assistant.",
            temperature=temperature,
            max_output_tokens=max_tokens
        )

        # Send the request to Gemini 2.0
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=Part.from_text(prompt),
            config=config
        )

        # Return the text response
        return response.text
    except Exception as e:
        return f"Error while communicating with Gemini 2.0: {str(e)}"


def chat_loop_gemini20(prompt, client, system_prompt, session_id):
    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    full_prompt = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation]
    )
    response = process_gemini20_chat(client, full_prompt, system_prompt)
    if response.startswith("Error:"):
        print(f"An error occurred: {response}")
    else:
        print(response)



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
        #print("Gemini:", response)
        print(response)
    #print("\n")
    #print()
    #print("> ")


def initialize_claude_client():
    ollama_url = read_config_parameter("options.network_settings.ollama_url") or "http://localhost:11434"
    base_url = f"{ollama_url.rstrip('/')}/v1"
    return anthropic.Anthropic(base_url=base_url, api_key="ollama")


def process_claude_chat(client, prompt, system_prompt=None):
    try:
        messages = [{"role": "user", "content": prompt}]
        response = client.messages.create(
            model="qwen3-coder",  # o el modelo que tengas en Ollama
            messages=messages,
            system=system_prompt or "",
            max_tokens=1000,
            temperature=0.7
        )
        return response.content[0].text
    except anthropic.APIError as e:
        return f"Error: Claude API request failed. Details: {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred. Details: {str(e)}"


def initialize_ollama_client():
    # No specific client initialization needed for basic HTTP requests
    pass


def chat_loop_claude(prompt, client, system_prompt, session_id):
    response_text = process_claude_chat(client, prompt, system_prompt)
    if response_text.startswith("Error:"):
        print(f"An error occurred: {response_text}")
    else:
        print(response_text)
    add_message(session_id, {"role": "assistant", "content": response_text})


def process_ollama_chat(prompt, system_prompt, ollama_url, model_name):
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "system": system_prompt
    }
    try:
        response = requests.post(f"{ollama_url}/api/generate", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Error: No response received from Ollama.")
    except requests.exceptions.RequestException as e:
        return f"Error: Request to Ollama API failed. Details: {str(e)}"
    except json.JSONDecodeError:
        return "Error: Invalid response received from Ollama."
    except Exception as e:
        return f"Error: An unexpected error occurred. Details: {str(e)}"


def initialize_euriai_client():
    """Initializes the EuriaAI client using credentials from the configuration."""
    try:
        from euriai import EuriaiClient
    except ImportError:
        raise ImportError("EuriaAI client not installed. Please install with 'pip install euriai'")

    api_key = read_config_parameter("options.network_settings.euriai_api_key")
    if not api_key:
        raise ValueError("EuriaAI API key not found in configuration.")

    model = read_config_parameter("options.network_settings.euriai_model")
    if not model:
        raise ValueError("EuriaAI model not found in configuration.")

    client = EuriaiClient(api_key=api_key, model=model)
    return client


def process_euriai_chat(client, full_prompt):
    """Processes a chat completion request with the EuriaAI client."""
    try:
        temperature = read_config_parameter("options.network_settings.euriai_temperature")
        max_tokens = read_config_parameter("options.network_settings.euriai_max_tokens")

        response = client.generate_completion(
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return "Error: Empty response from EuriaAI."
        return content
    except Exception as e:
        return f"Error: EuriaAI API request failed. Details: {str(e)}"


def chat_loop_euriai(prompt, system_prompt, session_id):
    """Manages the chat loop for the EuriaAI client."""
    try:
        client = initialize_euriai_client()

        # Load conversation history
        session_dir = os.path.join("data", "conversations", f"session_{session_id}")
        file_path = os.path.join(session_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                conversation_data = json.load(file)
                history = conversation_data.get("messages", [])
        else:
            history = []

        # Add current user message to history
        history.append({"role": "user", "content": prompt})

        # Prepare the full prompt with history
        full_prompt = f"{system_prompt}\n\n"
        for message in history:
            full_prompt += f"{message['role'].capitalize()}: {message['content']}\n"

        response = process_euriai_chat(client, full_prompt)

        # Save assistant's response to history
        history.append({"role": "assistant", "content": response})
        add_message(session_id, {"role": "assistant", "content": response})

        print(response)
    except (ValueError, ImportError) as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in the EuriaAI chat loop: {e}")





def chat_loop_ollama(prompt, system_prompt, session_id):
    import re
    from datetime import datetime

    ollama_url = read_config_parameter("options.network_settings.ollama_url") or "http://localhost:11434"
    ollama_model = read_config_parameter("options.network_settings.ollama_model")
    if not ollama_model:
        print("Error: Ollama model not specified in the configuration.")
        return

    # ðŸ’¡ Enforce strict JSON output instruction
    system_prompt += "\n\nIMPORTANT: Respond ONLY with a valid JSON object. Do NOT include explanations or text outside the JSON. Do NOT use markdown. The entire response must be pure JSON."

    # Prepare and send the request
    headers = {"Content-Type": "application/json"}
    data = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "system": system_prompt
    }

    try:
        if "/api/generate" in ollama_url:
            full_url = ollama_url
        else:
            full_url = f"{ollama_url.rstrip('/')}/api/generate"

        if not full_url.startswith("http"):
            full_url = "http://" + full_url

        response = requests.post(full_url, headers=headers, json=data)
        response.raise_for_status()
        # TODO: Only getting the content under 'response' but if it invents another it may not be properly parsing
        raw_response = response.json().get("response", "")

        # Save raw response to log for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/ollama_raw_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(raw_response)

        # Try direct JSON parse
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            # Salvage via regex
            match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except json.JSONDecodeError:
                    parsed = {"error": "Failed to parse embedded JSON", "raw": raw_response}
            else:
                parsed = {"error": "No JSON found in response", "raw": raw_response}

        # Output clean JSON for consumption by main app
        print(json.dumps(parsed))
        print("\n> ")
        print()
        print("> ")

    except requests.exceptions.RequestException as e:
        print(json.dumps({"error": f"Request to Ollama API failed: {str(e)}"}))
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {str(e)}"}))


class AIAssistant:
    """Class-based wrapper for AI assistant functionality."""
    def __init__(self):
        self.provider = read_config_parameter("options.network_settings.last_selected_llm_server_provider")
        self.server_url = read_config_parameter("options.network_settings.server_url")
        self.api_key = read_config_parameter("options.network_settings.api_key")
        self.system_prompt = "You are an intelligent assistant. You always flawlessly provide straight to the point well-reasoned answers that are both correct and helpful."

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate a response from the selected AI provider."""
        current_system = system_prompt or self.system_prompt
        session_id = datetime.now().strftime("%Y%m%d%H%M%S")

        # Capture stdout to return it as a string
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            if self.provider == "llama-cpp-python":
                client = initialize_client_with_parameters(self.server_url, self.api_key)
                model_path = find_gguf_file()
                chat_loop(prompt, client, model_path, current_system, session_id)
            elif self.provider == "gemini":
                client = initialize_gemini30_client()
                chat_loop_gemini30(prompt, client, current_system, session_id)
            elif self.provider == "claude":
                client = initialize_claude_client()
                chat_loop_claude(prompt, client, current_system, session_id)
            elif self.provider == "ollama":
                chat_loop_ollama(prompt, current_system, session_id)
            elif self.provider == "euriai":
                chat_loop_euriai(prompt, current_system, session_id)
            elif self.provider in ["openai", "lmstudio"]:
                client = initialize_client_with_parameters(self.server_url, self.api_key)
                chat_loop(prompt, client, "gpt-3.5-turbo", current_system, session_id)
            else:
                return f"Error: UNSUPPORTED LLM SERVER PROVIDER: {self.provider}"

        output = f.getvalue().strip()

        # Robustness: Handle JSON wrapping from certain providers (like Ollama)
        try:
            # Some providers might print extra newlines or prompts like "> "
            # Try to find the JSON part
            start = output.find('{')
            end = output.rindex('}') + 1
            if start != -1 and end != -1:
                json_part = output[start:end]
                data = json.loads(json_part)
            else:
                data = json.loads(output)

            if isinstance(data, dict):
                # If it's a dict with a 'response' or 'raw' key, that's likely the actual content
                if "response" in data:
                    return str(data["response"]).strip()
                if "raw" in data:
                    return str(data["raw"]).strip()
                # If it's a dict but not our expected format, it might be the AI's JSON response (e.g. for SpecGenerator)
                # In that case, we keep it as is (as a string)
        except (ValueError, json.JSONDecodeError):
            # Not a JSON string, return as is
            pass

        return output

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
        client = initialize_gemini30_client()
        chat_loop_gemini30(user_input, client, system_prompt, session_id)
    elif selected_llm_server_provider == "claude":
        client = initialize_claude_client()
        chat_loop_claude(user_input, client, system_prompt, session_id)
    elif selected_llm_server_provider == "ollama":
        chat_loop_ollama(user_input, system_prompt, session_id)
    elif selected_llm_server_provider == "euriai":
        chat_loop_euriai(user_input, system_prompt, session_id)
    elif selected_llm_server_provider in ["openai", "lmstudio"]:
        client = initialize_client_with_parameters(server_url, api_key)
        chat_loop(user_input, client, "gpt-3.5-turbo", system_prompt, session_id)
    else:
        print(f"UNSUPPORTED LLM SERVER PROVIDER: {selected_llm_server_provider}")


if __name__ == "__main__":
    main()

