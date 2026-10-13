import asyncio
import os
import sys
import json
from mcp import ClientSession, StdioServerParameters, McpError
from mcp.client.stdio import stdio_client

async def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    mcp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    runescript_path = os.environ.get("RUNESCRIPT_PATH", root_dir)

    env = dict(os.environ)
    env["RUNESCRIPT_PATH"] = runescript_path
    env["PYTHONPATH"] = f"{root_dir}:{mcp_dir}"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "cognito-stack.mcp-servers.runescript.src.server"],
        env=env
    )

    print("=== Hermes Agent Simulation ===")
    print("1. Connecting via stdio and initializing session...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_res = await session.list_tools()
            available_tools = [t.name for t in tools_res.tools]
            print(f"Connected. Discovered tools: {available_tools}\n")

            # Execution sequence
            print("2. Sequential Autonomous Code Generation and Execution:")

            # Step A: Generate
            print("   [Step A] Requesting code generation...")
            gen_res = await session.call_tool("generate_script", {"language": "python", "description": "Write a script that computes primes under 20"})
            raw_text = gen_res.content[0].text
            try:
                inner = json.loads(raw_text)
                if isinstance(inner, dict) and "content" in inner:
                    code = json.loads(inner["content"][0]["text"])
                else:
                    code = inner
            except Exception:
                code = raw_text

            print(f"   Generated Code:\n{code.strip()}")

            # Step B: Validate
            print("   [Step B] Validating syntax...")
            val_res = await session.call_tool("validate_syntax", {"script": code, "language": "python"})
            print(f"   Syntax Result: {val_res.content[0].text.strip()}")

            # Step C: Execute
            print("   [Step C] Executing script...")
            exec_res = await session.call_tool("execute_script", {"script": code, "language": "python", "timeout": 5})
            print(f"   Execution Result: {exec_res.content[0].text.strip()}\n")

            # Error Handling Scenarios
            print("3. Testing Error Handling Scenarios:")

            # Test 1: Non-existent tool
            print("   [Error Test 1] Calling non-existent tool 'git_commit'...")
            try:
                res = await session.call_tool("git_commit", {"message": "test"})
                print(f"   Response: {res.content[0].text.strip()}")
            except Exception as e:
                print(f"   Caught Exception: {e}")

            # Test 2: Invalid arguments (short description < 10 chars)
            print("   [Error Test 2] Calling 'generate_script' with invalid description ('short')...")
            try:
                res = await session.call_tool("generate_script", {"language": "python", "description": "short"})
                print(f"   Response: {res.content[0].text.strip()}")
            except Exception as e:
                print(f"   Caught Exception: {e}")

            # Test 3: Script timeout execution
            print("   [Error Test 3] Executing infinite loop with timeout=1s...")
            try:
                loop_code = "import time\nwhile True: time.sleep(0.1)"
                res = await session.call_tool("execute_script", {"script": loop_code, "language": "python", "timeout": 1})
                print(f"   Response: {res.content[0].text.strip()}")
            except Exception as e:
                print(f"   Caught Exception: {e}")

    print("\nSimulation complete.")

if __name__ == "__main__":
    asyncio.run(main())
