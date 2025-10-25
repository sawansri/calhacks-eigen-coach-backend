from tinydb import TinyDB
from pathlib import Path

DB_DIR = "db"

def get_db_path(db_name: str = "schedule") -> str:
    """Get database file path by name"""
    return f"{DB_DIR}/{db_name}_db.json"

def initialize_database(db_name: str = "schedule"):
    """Initialize a TinyDB database"""
    try:
        Path(DB_DIR).mkdir(exist_ok=True)
        db = TinyDB(get_db_path(db_name))
        print(f"Database '{db_name}' initialized successfully")
        db.close()
    except Exception as e:
        print(f"Error: {e}")

def get_db(db_name: str = "schedule"):
    """Get database connection"""
    return TinyDB(get_db_path(db_name))

def clear_database(db_name: str = "schedule"):
    """Clear all data from database while keeping the JSON file"""
    try:
        db = TinyDB(get_db_path(db_name))
        db.truncate()
        print(f"Database '{db_name}' cleared successfully")
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    initialize_database()
