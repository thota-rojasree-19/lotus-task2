import os
import pytest

@pytest.mark.asyncio
async def test_cross_fresher():
    # The goal is that another passing Product 004 API can be used by changing configuration only.
    # We verify that changing the environment variable would point the gateway to a new URL.
    # We can check that config variables are respected.
    
    from mcp_gateway.config import API_BASE_URL, OPENAPI_FILE
    # Since config is loaded once, we can just assert it uses the environment variables
    # which we set in conftest.py
    assert API_BASE_URL == os.environ.get("API_BASE_URL", "http://127.0.0.1:5000")
    assert OPENAPI_FILE == os.environ.get("OPENAPI_FILE", "./openapi.yaml")
