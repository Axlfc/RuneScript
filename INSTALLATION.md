# **Installation**

## **System Requirements**

### Minimum Requirements
- **OS**: Windows 10/11 or Linux (Ubuntu 20.04 or newer)
- **CPU**: Intel Core i5/AMD Ryzen 5 or better
- **RAM**: 8GB
- **Storage**: 4GB free disk space
- **Python**: 3.9 or newer

### Recommended Requirements
- **OS**: Windows 11 or Linux (Ubuntu 22.04 or newer)
- **CPU**: Intel Core i7/AMD Ryzen 7 or better
- **RAM**: 16GB
- **Storage**: 8GB free disk space
- **GPU**: NVIDIA RTX 2060 6GB or better (with CUDA support)
- **Python**: 3.9 or newer

> **Note**: NVIDIA GPU with CUDA support is recommended for optimal performance with AI features, Stable Diffusion, and audio generation.

---

## **Installing Dependencies**

### **Python**

#### On Windows:
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

#### On GNU/Linux:
1. Open a terminal.
2. Install Python:
   ```bash
   sudo apt-get update -y
   sudo apt-get install -y python3
   ```
3. Verify the installation:
   ```bash
   python3 --version
   ```

---

### **Git**

#### On Windows:
1. Open PowerShell.
2. Install Git:
   ```Powershell
   winget install -e --id Git.Git
   ```
3. Verify Git installation:
   ```Powershell
   git --version
   ```

#### On GNU/Linux:
1. Open a terminal.
2. Install Git:
   ```bash
   sudo apt-get update -y
   sudo apt-get install -y git
   ```
3. Verify Git installation:
   ```bash
   git --version
   ```

---

## **Setting up the Project**

1. Clone or fork the repository:
   ```bash
   git clone https://github.com/Axlfc/RuneScript.git
   ```
   If you forked the repository:
   ```bash
   git clone https://github.com/your_git_username/RuneScript.git
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
5. Install the required dependencies:
   - On Windows:
     ```bash
     .\venv\Scripts\pip install -r requirements.txt
     .\venv\Scripts\pip install -r src/models/requirements.txt
     ```
   - On macOS and Linux:
     ```bash
     venv/bin/pip install -r requirements.txt
     venv/bin/pip install -r src/models/requirements.txt
     ```

---

## **Setting up Models**

### Accessing Models on Hugging Face (TO-DO)

To use the `stable-audio-open-1.0` model for audio generation in RuneScript:

1. **Create a Hugging Face Account**:
   - Sign up [here](https://huggingface.co/join).

2. **Request Access to the Model**:
   - Visit the [stable-audio-open-1.0 model page](https://huggingface.co/stabilityai/stable-audio-open-1.0) and request access.

3. **Generate an API Token**:
   - Generate an API token in your Hugging Face profile settings.

4. **Download the Model Files**:
   - [stable-audio-open-1.0.ckpt](https://huggingface.co/stabilityai/stable-audio-open-1.0)
   - [sd-v1-4.ckpt](https://huggingface.co/CompVis/stable-diffusion-v-1-4-original/blob/main/sd-v1-4.ckpt)
   - [qwen2.5-coder-1.5b-q8_0.gguf](https://huggingface.co/ggerganov/Qwen2.5-Coder-1.5B-Q8_0-GGUF)

5. **Organize Models in the Repository**:
   ```bash
   mkdir -p src/models/model/text
   mkdir -p src/models/model/image
   mkdir -p src/models/model/audio
   ```
   - Place `.gguf` files in `src/models/model/text`.
   - Place Stable Diffusion models in `src/models/model/image`.
   - Place Stable Audio models in `src/models/model/audio`.

---

## **Running RuneScript**

### Setting up the AI Assistant

1. Place a valid `.gguf` file in `src/models/model/text`.
2. Start the AI assistant server:
   ```Powershell
   .\.venv\Scripts\python.exe -m llama_cpp.server --port 8004 --model .\src\models\model\qwen2.5-coder-1.5b-q8_0.gguf
   ```

### Run RuneScript

- On Windows:
  ```Powershell
  .\.venv\Scripts\python main.py
  ```
- On macOS and Linux:
  ```bash
  .venv/bin/python main.py
  ```