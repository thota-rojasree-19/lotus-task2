import os

OPENAPI_FILE = os.environ.get("OPENAPI_FILE", "./openapi.yaml")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:5000")
MCP_HOST = os.environ.get("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.environ.get("MCP_PORT", 8000))
