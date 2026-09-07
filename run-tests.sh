#!/usr/bin/env bash
# run-tests.sh — Full test pipeline for Product 004.
#
# Execution order (SOW-compliant):
#   Step 1: Validate openapi.yaml FIRST — contract must be valid before any
#           application logic executes against it.
#   Step 2: Reset the database — apply schema.sql then seed.sql.
#   Step 3: Run the contract harness — end-to-end HTTP-level checks.
#   Step 4: Run the pytest suite — unit/integration tests.
#
# Usage:
#   bash run-tests.sh
#
# Exit code: 0 on full pass, 1 on first failure.

set -e

echo "========================================================"
echo "  Product 004 — Restaurant API Test Runner"
echo "========================================================"
echo ""

echo "Step 1: Validating OpenAPI contract..."
python harness/validate_openapi.py
echo ""

echo "Step 2: Resetting database..."
python harness/reset_db.py
echo ""

echo "Step 3: Running contract harness..."
python harness/contract.py
echo ""

echo "Step 4: Running pytest suite..."
python -m pytest tests/ -v --tb=short
echo ""

echo "========================================================"
echo "  All steps passed."
echo "========================================================"
