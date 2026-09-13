import os
import sys
import yaml
import uvicorn
import httpx
from starlette.routing import Mount
from fastmcp import FastMCP
from mcp_gateway.config import OPENAPI_FILE, API_BASE_URL, MCP_HOST, MCP_PORT
from mcp_gateway.swagger import get_swagger_routes

def create_app():
    if not os.path.exists(OPENAPI_FILE):
        print(f"Error: OpenAPI file not found at {OPENAPI_FILE}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(OPENAPI_FILE, "r") as f:
            openapi_spec = yaml.safe_load(f)
    except Exception as e:
        print(f"Error: Failed to parse OpenAPI file: {e}", file=sys.stderr)
        sys.exit(1)

    # FastMCP uses the first server URL by default, or we can configure the client's base_url.
    # The requirement: Every MCP tool invocation must become an HTTP request to API_BASE_URL
    client = httpx.AsyncClient(base_url=API_BASE_URL)
    
    # Initialize FastMCP from OpenAPI spec
    mcp = FastMCP.from_openapi(
        name="Generic OpenAPI MCP Gateway",
        openapi_spec=openapi_spec,
        client=client
    )

    # FastMCP http_app returns a Starlette app
    app = mcp.http_app(transport="streamable-http", path="/mcp")

    # Mount Swagger UI
    app.routes.extend(get_swagger_routes())
    
    return mcp, app

mcp, app = create_app()

if __name__ == "__main__":
    uvicorn.run("mcp_gateway.server:app", host=MCP_HOST, port=MCP_PORT, log_level="info")
