import asyncio
import os
from mcp_gateway.server import mcp
from fastmcp.client import Client
from fastmcp.exceptions import ToolError

async def test():
    print("Testing API down...")
    try:
        async with Client(mcp) as client:
            res = await client.call_tool('listMenu', {})
            print("Response:", res)
    except ToolError as e:
        print("Caught ToolError:", e)
    except Exception as e:
        print("Caught Exception:", e)

asyncio.run(test())
