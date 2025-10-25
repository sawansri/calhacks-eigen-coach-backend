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

def get_all_memory_data() -> dict | str:
    """Helper function to retrieve all data in memory_db.
    
    Returns:
        Dictionary with memory data, or error message string
    """
    try:
        db = get_db("memory")
        records = db.all()
        
        if not records:
            return "Memory database is empty."
        
        # Return the first record (typically the only one)
        return records[0]
    
    except Exception as e:
        return f"Error retrieving memory data: {e}"

def get_skill_level_pairs_helper() -> list | str:
    """Helper function to get topic-skill level pairs from skill_level_db.
    
    Returns:
        List of tuples with (topic, skill_level), or error message string
    """
    try:
        db = get_db("skill_level")
        records = db.all()
        
        if not records:
            return "No skill level data found."
        
        skill_pairs = []
        for record in records:
            topic = record.get("topic", "N/A")
            skill_level = record.get("skill_level", "N/A")
            skill_pairs.append((topic, skill_level))
        
        return skill_pairs
    
    except Exception as e:
        return f"Error retrieving skill level data: {e}"

@mcp.tool()
async def get_skill_level_pairs() -> str:
    """Get list of topic-skill level pairs from skill_level_db."""
    result = get_skill_level_pairs_helper()
    
    if isinstance(result, str):
        return result
    
    formatted_results = []
    for topic, skill_level in result:
        formatted_results.append(f"Topic: {topic}, Skill Level: {skill_level}")
    
    return "Topic-Skill Level Pairs:\n" + "\n".join(formatted_results)

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
async def add_memory_entry(memory_entry: str) -> str:
    """Add a new entry to the memory array in memory_db.
    
    Args:
        memory_entry: String entry to add to the memory array
    
    Returns:
        Success or error message
    """
    try:
        db = get_db("memory")
        records = db.all()
        
        if not records:
            return "Error: Memory database is empty or not initialized."
        
        # Get the first (and typically only) record
        record = records[0]
        doc_id = record.doc_id
        
        # Get existing memory array
        memory_array = record.get("memory", [])
        
        # Add new entry
        memory_array.append(memory_entry)
        
        # Update the record
        db.update({"memory": memory_array}, doc_ids=[doc_id])
        
        return f"Memory entry successfully added: '{memory_entry}'"
    
    except Exception as e:
        return f"Error adding memory entry: {e}"

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

