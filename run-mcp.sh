#!/bin/bash
set -e

# Setup environment variables if not set
export OPENAPI_FILE=${OPENAPI_FILE:-./openapi.yaml}
export API_BASE_URL=${API_BASE_URL:-http://127.0.0.1:5000}
export MCP_HOST=${MCP_HOST:-127.0.0.1}
export MCP_PORT=${MCP_PORT:-8000}

echo "Starting MCP Gateway..."
echo "OpenAPI File: $OPENAPI_FILE"
echo "API Base URL: $API_BASE_URL"
echo "Listening on: $MCP_HOST:$MCP_PORT"

python -m mcp_gateway.server
