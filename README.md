# ScriptsEditor: Your Versatile Script Editor

[![License: GPL-2.0](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)](https://github.com/Axlfc/ScriptsEditor/releases)
[![Commits](https://img.shields.io/github/commit-activity/m/Axlfc/scriptseditor.svg?style=v2-blue)](https://github.com/Axlfc/ScriptsEditor/commits/master/)
[![Issues](https://img.shields.io/github/issues/Axlfc/scriptseditor.svg?style=v2-blue)](https://github.com/Axlfc/ScriptsEditor/issues)
[![Contributors](https://img.shields.io/github/contributors/Axlfc/scriptseditor.svg?style=v2-blue)](https://github.com/Axlfc/ScriptsEditor/graphs/contributors)
[![Stargazers](https://img.shields.io/github/stars/Axlfc/scriptseditor.svg?style=v2-blue)](https://github.com/Axlfc/ScriptsEditor/stargazers)

ScriptsEditor is a powerful and versatile script writing and editing platform built with Python, tailored for developers, scriptwriters, and coding enthusiasts. Designed to streamline your workflow, it offers advanced script execution capabilities, seamless Git integration, and an intelligent AI assistant for enhanced productivity. Whether you're managing cron jobs, editing scripts, or generating creative assets, ScriptsEditor provides a scalable, user-friendly environment to boost efficiency and manage complex projects effortlessly. Perfect for those seeking a dynamic tool that adapts to both code and creative needs.

![ScriptsEditor Screenshot](images/ScriptsStudio130.gif)

## Table of Contents
- [Features](#features)
- [Installation](#installation)
  - [Installing Dependencies](#installing-dependencies)
    - [Python](#python)
    - [Git](#git)
    - [llama-cpp-python](#llama-cpp-python)
  - [Setting up the Project](#setting-up-the-project)
- [Running ScriptsEditor](#running-scriptseditor)
- [Contributing](#contributing)
- [License](#license)

## Features
- Save, open, and edit scripts with an intuitive editor
- Script execution from within ScriptsEditor - Run immediately, Timeout, Entry Arguments...
- Advanced script execution with `at`, `crontab`, or Windows Scheduled Tasks
- **Shell integration**: Run custom system commands and manage tasks
- Basic Kanban application for project management
- System information display and program installation using **Winget**
- **Git Console**: Manage Git repositories from within the Git Console Window, including commits and branches _(work in progress)_
- **AI Assistant**: Multi-agent selection for local LLMs or external APIs (ChatGPT, Claude, etc.) _(work in progress)_
- Integration with **Stable Diffusion** and **Stable Audio** for image and audio generation _(work in progress)_
- Built-in **calculator window** _(work in progress)_

## Installation

### Installing Dependencies

#### Python

##### On Windows:
1. Open PowerShell.
2. Install Python:
   ```Powershell
   winget install -e --id Python.Python.3.9
   ```
3. Follow the installer instructions.
4. Ensure Python is accessible:
   ```Powershell
   python --version
   ```

##### On GNU/Linux:
1. Open terminal.
2. Install Python:
   ```bash
   sudo apt-get update -y
   sudo apt-get install -y python3
   ```
3. Check Python installation:
   ```bash
   python3 --version
   ```

#### Git

##### On Windows:
1. Open PowerShell.
2. Install Git:
   ```Powershell
   winget install -e --id Git.Git
   ```
3. Verify Git installation:
   ```Powershell
   git --version
   ```

##### On GNU/Linux:
1. Open terminal.
2. Install Git:
   ```bash
   sudo apt-get update -y
   sudo apt-get install -y git
   ```
3. Verify Git installation:
   ```bash
   git --version
   ```

### Setting up the Project

1. Clone the repository:
   ```bash
   git clone https://github.com/Axlfc/ScriptsEditor
   ```
2. Navigate to the project directory:
   ```bash
   cd ScriptsEditor
   ```
3. Create a virtual environment:
   - On Windows:
     ```Powershell
     python -m venv .venv
     ```
   - On macOS and Linux:
     ```bash
     python3 -m venv .venv
     ```
4. Activate the virtual environment:
   - On Windows:
     ```Powershell
     .\.venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source .venv/bin/activate
     ```
5. Install the required packages:
   - On Windows:
       ```bash
         .\venv\Scripts\pip install -r requirements.txt
         .\venv\Scripts\pip install -r src/models/requirements.txt
         .\venv\Scripts\pip install torchaudio==0.9.0 -f https://download.pytorch.org/whl/torch_stable.html
       ```

   - On macOS and Linux:
     ```bash
       venv/bin/pip install -r requirements.txt
       venv/bin/pip install -r src/models/requirements.txt
       venv/bin/pip install torchaudio==0.9.0 -f https://download.pytorch.org/whl/torch_stable.html
     ```
     
6. Install models:
  ## Accessing Models on Hugging Face  ```(TO-DO)```

To use the `stable-audio-open-1.0` model for audio generation in ScriptsEditor, follow these steps:

1. **Create a Hugging Face Account:**
   - If you haven't already, create an account on Hugging Face. You can sign up [here](https://huggingface.co/join).

2. **Request Access to the Model:**
   - Visit the [stable-audio-open-1.0 model page](https://huggingface.co/stabilityai/stable-audio-open-1.0).
   - Click on the "Request Access" button to request access to the model. This step may require accepting terms and conditions specific to the model's license.

3. **Generate an API Token:**
   - After your access request is approved, go to your Hugging Face profile settings.
   - Navigate to the API Tokens section and generate a new token. This token will be used to authenticate your access to the model from ScriptsEditor.

4. **Use the API Token in ScriptsEditor:**
   - Once you have your API token, you can use it in your ScriptsEditor setup to authenticate requests to the Hugging Face model.
   - Ensure that your token is securely stored and used according to best practices.

  - Get to download the model files 
    - [stable-audio-open-1.0.ckpt](https://huggingface.co/stabilityai/stable-audio-open-1.0)
    - [sd-v1-4.ckpt](https://huggingface.co/CompVis/stable-diffusion-v-1-4-original/blob/main/sd-v1-4.ckpt)
    - [llama-2-7b-chat.Q4_K_M.gguf](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)
  - Create a new folder in this repository in ```src/models``` named ```model```
  ```bash
      mkdir src/models/model
  ```
  - Create a new folder in this repository in ```src/models/model``` named ```text```
  ```bash
      mkdir src/models/model/text
  ```
  - Put the .gguf file in src/models/model/text directory.
  - Save Stable Diffusion model in src/models/model/image
  - Save Stable Audio model in src/models/model/audio 

We finished setting up ScriptsEditor.

## Running ScriptsEditor

### Setting up the AI Assistant

Before running ScriptsEditor, you need to set up the AI assistant server. Follow these steps:

1. Place a valid `.gguf` file into the folder `src/models/model`. In this example, the file used is `llama-2-7b-chat.Q4_K_M.gguf`.

2. Start the AI assistant server using the following command:
   ```Powershell
   .\.venv\Scripts\python.exe -m llama_cpp.server --port 8004 --model .\src\models\model\llama-2-7b-chat.Q4_K_M.gguf
   ```

After setting up and starting the AI assistant server, you can run ScriptsEditor by executing the `main.py` script.

- On Windows:
  ```Powershell
  .\.venv\Scripts\python main.py
  ```
- On macOS and Linux:
  ```bash
  .venv/bin/python main.py
  ```

## Contributing

We welcome contributions! If you'd like to contribute to ScriptsEditor, please check our [contribution guidelines](CONTRIBUTING.md).

## License

ScriptsEditor is open-source and licensed under the [GPL-2.0](LICENSE).

## TO-DO:
- [] Implement whisper.cpp to be able to talk to ScriptsEditor
- [] Implement TTS (Accessibility)

