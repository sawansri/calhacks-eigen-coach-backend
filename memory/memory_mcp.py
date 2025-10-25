"""
Memory MCP server using MySQL database.
Provides tools for accessing student memory, calendar, and skill levels.
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any
import sys
import logging
import json

# Add parent directory to path for imports
sys.path.insert(0, '/Users/joe/repostories/calhacks/backend')

from database.db_helpers import (
    get_student_memory,
    add_student_memory,
    get_calendar_entry,
    get_skill_levels,
    set_skill_level,
)

# Configure logging
log = logging.getLogger("memory_mcp")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)


# Helper functions for direct data access
def get_skill_level_pairs_helper() -> list:
    """Helper to get skill level pairs for a student.
    
    Returns:
        List of (topic, skill_level) tuples
    """
    try:
        return get_skill_levels()
    except Exception as e:
        log.error(f"Error in get_skill_level_pairs_helper: {e}")
        return []


# MCP Tools
@tool(
    "get_skill_level_pairs",
    "Get topic-skill level pairs for the student",
    {}
)
async def get_skill_level_pairs_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get skill level pairs for a student."""
    try:
        pairs = get_skill_level_pairs_helper()
        
        if not pairs:
            text = "No skill levels found."
        else:
            formatted = [f"Topic: {topic}, Skill Level: {level}" for topic, level in pairs]
            text = "Skill Levels:\n" + "\n".join(formatted)
        
        return {"content": [{"type": "text", "text": text}]}
        
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@tool(
    "get_topics_by_date",
    "Get topics and question count for a specific date",
    {"date": str}
)
async def get_topics_by_date_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Get calendar entry for a date."""
    date = args.get("date", "")
    
    try:
        entry = get_calendar_entry(date)
        
        if not entry:
            text = f"No schedule found for {date}."
        else:
            topics_str = ", ".join(entry['topics'])
            text = f"Date: {entry['date']}\nTopics: {topics_str}\nQuestions: {entry['n_questions']}"
        
        return {"content": [{"type": "text", "text": text}]}
        
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@tool(
    "add_memory_entry",
    "Add a memory note for the student",
    {"memory_entry": str}
)
async def add_memory_entry_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Add memory entry for a student."""
    memory_entry = args.get("memory_entry", "")
    
    try:
        success = add_student_memory(memory_entry)
        
        if success:
            text = f"Memory added: '{memory_entry}'"
        else:
            text = "Failed to add memory entry"
        
        return {"content": [{"type": "text", "text": text}]}
        
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@tool(
    "update_skill_level",
    "Update or set skill level for a topic",
    {"topic": str, "skill_level": int}
)
async def update_skill_level_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Update skill level for a student topic."""
    topic = args.get("topic", "")
    skill_level = args.get("skill_level", 0)
    
    try:
        success = set_skill_level(topic, skill_level)
        
        if success:
            text = f"Skill level updated: {topic} = {skill_level}"
        else:
            text = "Failed to update skill level"
        
        return {"content": [{"type": "text", "text": text}]}
        
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Create MCP server
memory_server = create_sdk_mcp_server(
    "memory-manager",
    "1.0.0",
    tools=[
        get_skill_level_pairs_tool,
        get_topics_by_date_tool,
        add_memory_entry_tool,
        update_skill_level_tool
    ]
)




if __name__ == "__main__":
    log.info("Starting memory MCP server (MySQL backend)")
    memory_server.run()
