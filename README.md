# **RuneScript: Your Gateway to Intelligent Script Editing and Beyond**

[![License: GPL-2.0](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)](https://github.com/Axlfc/ScriptsEditor/releases)
[![Commits](https://img.shields.io/github/commit-activity/m/Axlfc/scriptseditor.svg?style=v2-blue)](https://github.com/Axlfc/ScriptsEditor/commits/master/)
[![Issues](https://img.shields.io/github/issues/Axlfc/scriptseditor.svg?style=v2-blue)](https://github.com/Axlfc/ScriptsEditor/issues)
[![Contributors](https://img.shields.io/github/contributors/Axlfc/scriptseditor.svg?style=v2-blue)](https://github.com/Axlfc/ScriptsEditor/graphs/contributors)
[![Stargazers](https://img.shields.io/github/stars/Axlfc/scriptseditor.svg?style=v2-blue)](https://github.com/Axlfc/ScriptsEditor/stargazers)

RuneScript redefines how you create, edit, and manage scripts. Built with Python, it’s more than a script editor—it's a fully integrated platform offering advanced AI capabilities, intuitive Git management, creative tools, and powerful automation. Whether you're a developer, designer, or technical writer, RuneScript is designed to streamline workflows and enable collaboration on a whole new level.  

**Join us on our journey to innovate, create, and revolutionize script editing!**

---

## **Table of Contents**
- [System Requirements](#system-requirements)
- [Features](#features)
- [Planned Features](#planned-features)
- [Installation](#installation)
- [Running RuneScript](#running-runescript)
- [How to Contribute](#how-to-contribute)
- [Roadmap & Vision](#roadmap--vision)
- [License](#license)

---

## **System Requirements**

### Minimum Requirements
- **OS**: Windows 10/11 or Linux (Ubuntu 20.04+)
- **CPU**: Intel Core i5/AMD Ryzen 5
- **RAM**: 8GB
- **Storage**: 4GB free space
- **Python**: 3.9+

### Recommended Requirements
- **OS**: Windows 11 or Linux (Ubuntu 22.04+)
- **CPU**: Intel Core i7/AMD Ryzen 7
- **RAM**: 16GB
- **Storage**: 8GB free space
- **GPU**: NVIDIA RTX 2060 6GB (CUDA support)
- **Python**: 3.9+

---

## **Features**

### Core Functionality:
1. **Versatile Script Editor**:
   - Save, open, and edit scripts with an intuitive editor.
   - Execute scripts directly with runtime arguments, timeouts, and environment setup.
   - Advanced job scheduling using `crontab` or Windows Task Scheduler.

2. **Shell and Git Integration**:
   - Run custom system commands from the editor.
   - Manage repositories with built-in Git functionality:
     - Commits, branches, and merges via a user-friendly console.

3. **AI-Enhanced Productivity**:
   - Multi-agent assistant with support for local models (llama-cpp-python) and external APIs (ChatGPT, Claude, etc.).
   - Intelligent prompt management to improve and reuse common tasks.
   - Integrated Stable Diffusion and Stable Audio for generating images and audio.

4. **Built-in Utilities**:
   - Kanban board for project and task management.
   - System monitoring dashboard with quick installation via Winget.

---

## **Planned Features**

### **Big Picture Vision**  
RuneScript aims to become the ultimate workspace for developers, creative professionals, and technical teams. Here’s what’s coming next:

1. **1-Click Deployment**:
   - Deploy projects seamlessly across AWS, Azure, Google Cloud, or on-prem servers.
   - Generate Dockerfiles and Kubernetes manifests automatically.
   - Integrated CI/CD pipeline management.

2. **Audio and Visual Creativity**:
   - Integration with **Stable Diffusion CPP** for image generation.
   - **Whisper** integration for speech-to-text functionality.
   - Advanced **Stable Audio** backend for high-quality audio synthesis.

3. **Collaboration Tools**:
   - Real-time co-editing for remote teams.
   - Role-based access control and task management.

4. **Marketplace & Plugin System**:
   - Download and share community-made plugins, templates, and AI tools.

---

## **Installation**

### Dependencies

#### Python
- **Windows**:
  ```Powershell
  winget install -e --id Python.Python.3.9
  ```
- **Linux**:
  ```bash
  sudo apt update && sudo apt install python3
  ```

#### Git
- **Windows**:
  ```Powershell
  winget install -e --id Git.Git
  ```
- **Linux**:
  ```bash
  sudo apt update && sudo apt install git
  ```

#### Additional Tools
Install AI models, dependencies, and configure as detailed in our [documentation](docs/INSTALLATION.md).

---

## **Running RuneScript**

### Claude for Projects and autonomous development

Open **Tools → AI Assistant Options → AI Assistant Options** (or press
`Ctrl+Alt+O`), select `claude`,
and enter your Anthropic API key, workspace ID (`wrkspc_...`) and model ID.
The workspace ID is required for keys that are not scoped to a workspace; a
workspace-scoped key can leave it blank. Leave the key field blank when saving
to keep an existing key. The model defaults to `claude-sonnet-4-6` and can be
changed to a model available to your account. Select `ollama` for local models.

The settings are stored in the ignored `.env` file in the RuneScript root.
The key is stored there as plaintext, so keep the file private and never commit
or share it. Alternatively set `ANTHROPIC_API_KEY`, optional
`ANTHROPIC_WORKSPACE_ID`, and optional `ANTHROPIC_MODEL` in the environment
before starting RuneScript; environment values take precedence over `.env`.
The project interpreter must have the packages in `requirements.txt` installed.
An Anthropic API key, model access, and available API credit are needed for a
live test. A Claude subscription alone does not supply API access.

### **Setup the AI Assistant**

1. Download your preferred `.gguf` model for local use:
   - [Hugging Face Link](https://huggingface.co/models)
   - Example: `qwen2.5-coder-1.5b-q8_0.gguf`.

2. Start the AI server:
   ```Powershell
   .venv\Scripts\python -m llama_cpp.server --port 8004 --model .\src\models\model\qwen2.5-coder-1.5b-q8_0.gguf
   ```

### **Launch RuneScript**

- **Windows**:
  ```Powershell
  .venv\Scripts\python main.py
  ```
- **Linux**:
  ```bash
  .venv/bin/python main.py
  ```

---

## **How to Contribute**

We value the contributions of developers, designers, and visionaries.  
- Check out our [contribution guidelines](CONTRIBUTING.md).
- Join discussions and report issues [here](https://github.com/Axlfc/scriptseditor/issues).
- Fork and submit pull requests to enhance RuneScript.

---

## **Roadmap & Vision**

RuneScript is a collaborative, dynamic project with a bold future. Here’s what we’re working toward:

- **Collaborative Innovation**:
  - Join a community of forward-thinking engineers and designers building the future.
  - Contribute to open-source modules that shape the industry.

- **Developer Empowerment**:
  - Unlock potential through AI-enhanced workflows and intelligent assistants.
  - Bridge technical barriers with low-code/no-code integrations.

- **Sustainable Growth**:
  - Foster a marketplace for extensions, plugins, and templates.
  - Drive funding and support from individuals and enterprises who believe in our mission.

---

## **Join the Movement**

### Why RuneScript?  
- **Efficiency**: Simplify tasks with AI-driven tools.  
- **Collaboration**: Empower teams to achieve more, faster.  
- **Innovation**: Build, share, and evolve the tools of tomorrow.

### **Get Involved**  
- ⭐ **Star us on GitHub**: Show your support and help us grow.  
- 🤝 **Collaborate**: Share your expertise and contribute to the future.  
- 🚀 **Invest**: Partner with us to accelerate development and reach new heights.

Let’s transform how the world writes, manages, and executes scripts—together.

---  
### **License**
RuneScript is licensed under the [GPL-2.0](LICENSE).  

---  

We’d love to hear your thoughts and ideas! Join us on this exciting journey.  
**Together, let’s shape the future of intelligent scripting.** 🌟

