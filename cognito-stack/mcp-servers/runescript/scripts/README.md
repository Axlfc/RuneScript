# RuneScript MCP Server Verification Test Suite

This directory contains automated verification scripts to audit and validate the RuneScript MCP Server via stdio JSON-RPC protocol.

## Prerequisites

Ensure virtual environment is active and `RUNESCRIPT_PATH` is set to the RuneScript repository root:

```bash
export RUNESCRIPT_PATH=/path/to/RuneScript
```

## Running the Tests

### 1. Minimal MCP Client Handshake & Tool Chain Test (FASE 3)

Tests connection, `initialize`, `tools/list`, and sequential invocation of `generate_script` -> `execute_script` -> `validate_syntax` -> `list_templates`:

```bash
python scripts/mcp_test_client.py
```

### 2. Hermes Agent Simulation & Error Handling Test (FASE 4)

Simulates Hermes Agent interacting over stdio, verifying sequential execution and error handling (unknown tools, invalid schemas, execution timeouts):

```bash
python scripts/hermes_simulator.py
```
