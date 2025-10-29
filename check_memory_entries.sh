#!/bin/bash

# Database Memory Entries Checker Script
# This script displays all memory entries stored in the database

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Run the memory entries check
python3 check_memory_entries.py

exit $?
