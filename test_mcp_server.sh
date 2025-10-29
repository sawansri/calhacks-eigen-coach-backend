#!/bin/bash

# MCP Server Test Runner Script
# This script runs the Python test to verify the MCP server is working

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       MCP Database Server Verification Script              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "📝 Starting MCP server tests..."
echo ""

# Run the test script
python3 test_mcp_server.py

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ MCP server verification complete"
else
    echo "❌ MCP server verification failed"
fi

exit $EXIT_CODE
