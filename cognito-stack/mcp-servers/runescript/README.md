# RuneScript MCP Server

This server exposes RuneScript functionalities through the Model Context Protocol (MCP).

## Setup

1. **Clone RuneScript**:
   ```bash
   git clone https://github.com/Axlfc/RuneScript.git
   cd RuneScript
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Create a `.env` file in this directory and set the path to your RuneScript installation:
   ```env
   RUNESCRIPT_PATH=/path/to/your/RuneScript
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**:
   ```bash
   python -m src.server
   ```
