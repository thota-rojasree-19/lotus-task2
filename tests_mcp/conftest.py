import os
import pytest
import sqlite3
from mcp_gateway.server import create_app

# Update config for tests
os.environ["OPENAPI_FILE"] = "./openapi.yaml"
os.environ["API_BASE_URL"] = "http://127.0.0.1:5000"

# Note: We need the actual Product 004 backend running on port 5000 for integration tests,
# or we can mock it, but the requirement implies testing the flow through the gateway.
# "tests_mcp/test_workflow.py: listMenu ... All of these must happen THROUGH MCP"
# The test runner script `run-tests-mcp.sh` will start the backend.

import pytest_asyncio

@pytest.fixture(scope="session")
def mcp_server():
    from mcp_gateway.server import mcp
    return mcp

@pytest_asyncio.fixture(scope="function")
async def mcp_client(mcp_server):
    # Using FastMCP's built-in SDK client wrapper if available, or just standard mcp client.
    # FastMCP provides a ContextManager for Client:
    from fastmcp.client import Client
    # Client initialized with a FastMCP instance automatically uses a direct transport
    async with Client(mcp_server) as client:
        yield client

@pytest.fixture(autouse=True)
def reset_db():
    import subprocess
    subprocess.run(["python", "harness/reset_db.py"], check=True)

