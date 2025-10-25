from typing import Any, List
from tinydb import TinyDB, Query
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("schedule_manager")

# Database paths
DB_DIR = "db"

def get_db_path(db_name: str) -> str:
    """Get database file path by name"""
    return f"{DB_DIR}/{db_name}_db.json"

def get_db(db_name: str) -> TinyDB:
    """Get TinyDB connection"""
    return TinyDB(get_db_path(db_name))

@mcp.tool()
async def get_skill_level_pairs() -> str:
    """Get list of topic-skill level pairs from skill_level_db."""
    try:
        db = get_db("skill_level")
        records = db.all()
        
        if not records:
            return "No skill level data found."
        
        formatted_results = []
        for record in records:
            formatted = f"Topic: {record.get('topic', 'N/A')}, Skill Level: {record.get('skill_level', 'N/A')}"
            formatted_results.append(formatted)
        
        return "Topic-Skill Level Pairs:\n" + "\n".join(formatted_results)
    
    except Exception as e:
        return f"Error retrieving skill level data: {e}"

@mcp.tool()
async def get_all_memory_data() -> str:
    """Retrieve all data in memory_db."""
    try:
        db = get_db("memory")
        records = db.all()
        
        if not records:
            return "Memory database is empty."
        
        formatted_results = []
        for i, record in enumerate(records, 1):
            formatted = f"Record {i}: {record}"
            formatted_results.append(formatted)
        
        return "All Memory Data:\n" + "\n".join(formatted_results)
    
    except Exception as e:
        return f"Error retrieving memory data: {e}"

@mcp.tool()
async def get_topics_by_date(date: str) -> str:
    """Get list of topics and number of questions scheduled for a specific date.
    
    Args:
        date: Date string in format YYYY-MM-DD
    
    Returns:
        Topics and question count for that date, or a message if no schedule found
    """
    try:
        db = get_db("calendar")
        records = db.all()
        
        # Search for the record with matching date
        for record in records:
            if record.get("date") == date:
                topics = record.get("topics", [])
                n_questions = record.get("n_questions", 0)
                if not topics:
                    return f"No topics scheduled for {date}."
                topics_str = ", ".join(topics)
                return f"Topics for {date}: {topics_str} | Number of questions: {n_questions}"
        
        return f"No schedule found for {date}."
    
    except Exception as e:
        return f"Error retrieving topics for date {date}: {e}"

@mcp.tool()
async def write_to_database(db_name: str, data: str) -> str:
    """Write data to any one of these databases.
    
    Args:
        db_name: Database name (skill_level, memory, or calendar)
        data: JSON string of data to insert
    """
    try:
        import json
        db = get_db(db_name)
        data_dict = json.loads(data)
        db.insert(data_dict)
        return f"Data successfully written to {db_name}_db"
    
    except json.JSONDecodeError:
        return "Error: Invalid JSON format"
    except Exception as e:
        return f"Error writing to database: {e}"


if __name__ == "__main__":
    mcp.run()

