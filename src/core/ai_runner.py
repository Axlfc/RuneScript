import subprocess
import logging

from src.controllers.parameters import read_config_parameter

try:
    interpreter_directory = read_config_parameter("options.project_settings.current_interpreter")
except Exception as e:
    print("AI RUNNER INTERPRETER NOT FOUND.\n", e)


def run_ai_prompt(ai_script_path: str, input_json: str, python_executable = interpreter_directory) -> str:
    try:
        print("MY PYTHON CUSTOM EXECUTABLE:")
        interpreter_directory = read_config_parameter("options.project_settings.current_interpreter")
        print("--->", interpreter_directory)
        command = [python_executable, ai_script_path, input_json]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"AI script exited with code {process.returncode}:\n{stderr.strip()}")

        if stderr:
            logging.warning(f"AI script stderr:\n{stderr.strip()}")

        return stdout.strip()

    except Exception as e:
        logging.error(f"AI runner failed: {e}")
        raise
