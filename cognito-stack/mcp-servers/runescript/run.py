#!/usr/bin/env python3
import sys
import os
import asyncio

# Prevent collision with top-level 'src' of RuneScript root
mcp_dir = os.path.dirname(os.path.abspath(__file__))
if mcp_dir in sys.path:
    sys.path.remove(mcp_dir)
sys.path.insert(0, mcp_dir)

from src.server import main

if __name__ == "__main__":
    asyncio.run(main())
