import asyncio
import os
import sys
import json
from mcp import ClientSession, StdioServerParameters
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

    print("Connecting to RuneScript MCP Server via stdio...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize
            init_result = await session.initialize()
            print("=== Handshake / Initialize Result ===")
            print(json.dumps(init_result.model_dump(), indent=2, default=str))
            print()

            # 2. List tools
            tools_result = await session.list_tools()
            print("=== Available Tools ===")
            for tool in tools_result.tools:
                print(f"- {tool.name}: {tool.description}")
            print()

            # 3. Sequence a -> b -> c -> d
            # a) generate_script
            print("=== Call a) generate_script ===")
            gen_args = {
                "language": "python",
                "description": "create a hello world script"
            }
            gen_res = await session.call_tool("generate_script", gen_args)
            raw_text = gen_res.content[0].text
            print("Response raw text:", raw_text)

            # The MCP server wraps results in {"content": [{"type": "text", "text": json_dump}]}
            # Parse inner text string
            parsed_inner = json.loads(raw_text)
            if isinstance(parsed_inner, dict) and "content" in parsed_inner:
                generated_script = json.loads(parsed_inner["content"][0]["text"])
            else:
                generated_script = parsed_inner

            print("\nExtracted Generated Script:")
            print(repr(generated_script))
            print()

            # b) execute_script
            print("=== Call b) execute_script ===")
            exec_args = {
                "script": generated_script,
                "language": "python",
                "timeout": 10
            }
            exec_res = await session.call_tool("execute_script", exec_args)
            print("Response:", exec_res.content[0].text)
            print()

            # c) validate_syntax
            print("=== Call c) validate_syntax ===")
            val_args = {
                "script": generated_script,
                "language": "python"
            }
            val_res = await session.call_tool("validate_syntax", val_args)
            print("Response:", val_res.content[0].text)
            print()

            # d) list_templates
            print("=== Call d) list_templates ===")
            tmpl_res = await session.call_tool("list_templates", {})
            print("Response:", tmpl_res.content[0].text)
            print()

if __name__ == "__main__":
    asyncio.run(main())
