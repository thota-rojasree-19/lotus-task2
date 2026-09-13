#!/bin/bash

echo "Starting Product 005 Acceptance Flow..."

echo "1. Baseline verification..."
python harness/validate_openapi.py || { echo "OpenAPI validation failed"; exit 1; }
python harness/contract.py || { echo "Contract verification failed"; exit 1; }
python -m pytest tests/ || { echo "Product 004 tests failed"; exit 1; }

echo "2. Starting Product 004 Backend..."
python harness/reset_db.py
export FLASK_APP=src.app:app
export FLASK_RUN_PORT=5000
python -m flask run &
FLASK_PID=$!
sleep 2

echo "3. Running MCP tests..."
export OPENAPI_FILE=./openapi.yaml
export API_BASE_URL=http://127.0.0.1:5000

python -m pytest tests_mcp/ -v
TEST_RESULT=$?

echo "Cleaning up..."
kill $FLASK_PID

if [ $TEST_RESULT -eq 0 ]; then
  echo "================================================"
  echo "  PRODUCT 005 MCP RESULTS: ALL TESTS PASSED"
  echo "================================================"
else
  echo "================================================"
  echo "  PRODUCT 005 MCP RESULTS: TESTS FAILED"
  echo "================================================"
fi
exit $TEST_RESULT
