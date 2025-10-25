"""
Unified database initialization for Eigen Coach.
Creates database, tables, and sets up connection pool.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import DatabaseManager


def initialize_database():
    """
    Initialize the Eigen Coach database.
    Creates connection pool and runs migrations.
    """
    try:
        print("[Database] Initializing connection pool and running migrations...")
        DatabaseManager.initialize()
        print("[Database] ✓ Initialization complete")
        return True
    except Exception as e:
        print(f"[Database] ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = initialize_database()
    sys.exit(0 if success else 1)
