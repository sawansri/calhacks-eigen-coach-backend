from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any
import sys
import os
import logging
import json
from tinydb import TinyDB, Query

# Configure logging
log = logging.getLogger("memory_mcp")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

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


# Define tools using the @tool decorator
@tool("get_skill_level_pairs", "Get list of topic-skill level pairs from skill_level_db", {})
async def get_skill_level_pairs(args: dict[str, Any]) -> dict[str, Any]:
    """Get list of topic-skill level pairs from skill_level_db."""
    result = get_skill_level_pairs_helper()
    
    if isinstance(result, str):
        text = result
    else:
        formatted_results = []
        for topic, skill_level in result:
            formatted_results.append(f"Topic: {topic}, Skill Level: {skill_level}")
        text = "Topic-Skill Level Pairs:\n" + "\n".join(formatted_results)
    
    return {
        "content": [{
            "type": "text",
            "text": text
        }]
    }


@tool("get_topics_by_date", "Get list of topics and number of questions scheduled for a specific date", {"date": str})
async def get_topics_by_date(args: dict[str, Any]) -> dict[str, Any]:
    """Get list of topics and number of questions scheduled for a specific date.
    
    Args:
        date: Date string in format YYYY-MM-DD
    
    Returns:
        Topics and question count for that date, or a message if no schedule found
    """
    date = args.get("date", "")
    
    try:
        db = get_db("calendar")
        records = db.all()
        
        # Search for the record with matching date
        for record in records:
            if record.get("date") == date:
                topics = record.get("topics", [])
                n_questions = record.get("n_questions", 0)
                if not topics:
                    text = f"No topics scheduled for {date}."
                else:
                    topics_str = ", ".join(topics)
                    text = f"Topics for {date}: {topics_str} | Number of questions: {n_questions}"
                
                return {
                    "content": [{
                        "type": "text",
                        "text": text
                    }]
                }
        
        text = f"No schedule found for {date}."
        
    except Exception as e:
        text = f"Error retrieving topics for date {date}: {e}"
    
    return {
        "content": [{
            "type": "text",
            "text": text
        }]
    }


@tool("add_memory_entry", "Add a new entry to the memory array in memory_db", {"memory_entry": str})
async def add_memory_entry(args: dict[str, Any]) -> dict[str, Any]:
    """Add a new entry to the memory array in memory_db.
    
    Args:
        memory_entry: String entry to add to the memory array
    
    Returns:
        Success or error message
    """
    memory_entry = args.get("memory_entry", "")
    
    try:
        db = get_db("memory")
        records = db.all()
        
        if not records:
            text = "Error: Memory database is empty or not initialized."
        else:
            # Get the first (and typically only) record
            record = records[0]
            doc_id = record.doc_id
            
            # Get existing memory array
            memory_array = record.get("memory", [])
            
            # Add new entry
            memory_array.append(memory_entry)
            
            # Update the record
            db.update({"memory": memory_array}, doc_ids=[doc_id])
            
            text = f"Memory entry successfully added: '{memory_entry}'"
        
    except Exception as e:
        text = f"Error adding memory entry: {e}"
    
    return {
        "content": [{
            "type": "text",
            "text": text
        }]
    }


@tool("write_to_database", "Write data to any one of the databases", {"db_name": str, "data": str})
async def write_to_database(args: dict[str, Any]) -> dict[str, Any]:
    """Write data to any one of these databases.
    
    Args:
        db_name: Database name (skill_level, memory, or calendar)
        data: JSON string of data to insert
    """
    db_name = args.get("db_name", "")
    data_str = args.get("data", "")
    
    try:
        db = get_db(db_name)
        data_dict = json.loads(data_str)
        db.insert(data_dict)
        text = f"Data successfully written to {db_name}_db"
        
    except json.JSONDecodeError:
        text = "Error: Invalid JSON format"
    except Exception as e:
        text = f"Error writing to database: {e}"
    
    return {
        "content": [{
            "type": "text",
            "text": text
        }]
    }


# Create the SDK MCP server with all tools
memory_server = create_sdk_mcp_server(
    name="memory-manager",
    version="1.0.0",
    tools=[
        get_skill_level_pairs,
        get_topics_by_date,
        add_memory_entry,
        write_to_database
    ]
)


if __name__ == "__main__":
    try:
        log.info("Starting Memory MCP Server...")
        log.info(f"Working directory = {os.getcwd()}")
        log.info(f"DB_DIR = {DB_DIR}")
        
        # Verify databases exist
        for db_name in ["memory", "calendar", "skill_level"]:
            db_path = get_db_path(db_name)
            if os.path.exists(db_path):
                log.info(f"Found {db_name}_db.json")
            else:
                log.warning(f"{db_name}_db.json not found at {db_path}")
        
        log.info("Starting memory_server...")
        memory_server.run()
        log.info("memory_server completed")
        
    except KeyboardInterrupt:
        log.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        log.error(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

