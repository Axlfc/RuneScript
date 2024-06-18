# ScriptsEditor: Your Versatile Script Editor

ScriptsEditor is an innovative script editing platform, offering advanced features and tools for developers, scriptwriters, and coding enthusiasts. With its rich set of functionalities, including syntax highlighting, version control integration, and AI assistant, ScriptsEditor stands out as a versatile and user-friendly environment for coding and script management.


Help us improve ScriptsEditor by tackling the [following tasks](https://github.com/Axlfc/ScriptsEditor/issues).


## Getting Started

To get started with ScriptsEditor, you'll need to set up a Python environment and install the required dependencies.

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

### Installation

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
     ```bash
     .\venv\Scripts\python -m venv venv
     ```

   - On macOS and Linux:
     ```bash
     venv/bin/python -m venv venv
     ```

4. Activate the virtual environment:

   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```

   - On macOS and Linux:
     ```bash
     source venv/bin/activate
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

### Running ScriptsEditor

After installing the dependencies, you can run ScriptsEditor by executing the main script file.

   - On Windows:
       ```bash
         .\venv\Scripts\python main.py
       ```

   - On macOS and Linux:
     ```bash
       venv/bin/python main.py
     ```

## Contributing

We welcome contributions! If you'd like to contribute to ScriptsEditor, please check our [contribution guidelines](CONTRIBUTING.md).

## License

ScriptsEditor is open-source and licensed under the [GPL-2.0](LICENSE).

## TO-DO:
- [] Implement whisper.cpp to be able to talk to ScriptsEditor
- [] Implement TTS (Accessibility)

