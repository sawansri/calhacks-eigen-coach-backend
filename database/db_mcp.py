"""
Unified MCP server for Eigen Coach database.
Provides tools for questions, student memory, calendar, and skill levels.
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any
import sys
import logging
import json

# Add parent directory to path
sys.path.insert(0, '/Users/joe/repostories/calhacks/backend')

from database.db import DatabaseManager
from database.db_helpers import (
    get_or_create_student,
    get_student_memory,
    add_student_memory,
    get_calendar_entry,
    set_calendar_entry,
    get_skill_levels,
    set_skill_level
)

# Configure logging
log = logging.getLogger("db_mcp")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)


# ============================================================================
# Question Bank Tools
# ============================================================================

@tool(
    "get_question_by_topic",
    "Get questions from the database by topic tag",
    {"topic": str}
)
async def get_question_by_topic(args: dict[str, Any]) -> dict[str, Any]:
    """Get questions for a specific topic."""
    topic = args.get("topic", "")
    
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT * FROM questions 
            WHERE topic_tag1 = %s OR topic_tag2 = %s OR topic_tag3 = %s
        """
        cursor.execute(query, (topic, topic, topic))
        results = cursor.fetchall()
        
        if not results:
            text = f"No questions found for topic: {topic}"
        else:
            formatted = []
            for row in results:
                formatted.append(f"""
Question: {row['question_prompt']}
Answer: {row['answer']}
Explanation: {row['explanation']}
Difficulty: {row['difficulty']}
Topics: {row['topic_tag1']}, {row['topic_tag2']}, {row['topic_tag3']}
Asked: {row['has_been_asked']}
---""")
            text = "\n".join(formatted)
        
        cursor.close()
        conn.close()
        return {"content": [{"type": "text", "text": text}]}
        
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@tool(
    "get_unique_topics",
    "Get all unique topics with their average difficulty scores",
    {}
)
async def get_unique_topics(args: dict[str, Any]) -> dict[str, Any]:
    """Get all unique topics from the question bank."""
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        # Get unique topics
        query = """
            SELECT DISTINCT topic_tag1 FROM questions 
            UNION 
            SELECT DISTINCT topic_tag2 FROM questions
            UNION
            SELECT DISTINCT topic_tag3 FROM questions
            WHERE topic_tag3 IS NOT NULL
            ORDER BY topic_tag1
        """
        cursor.execute(query)
        topics_results = cursor.fetchall()
        
        if not topics_results:
            text = "No topics found."
        else:
            topics = [row[0] for row in topics_results if row[0]]
            topic_scores = []
            
            # Calculate average difficulty for each topic
            for topic in topics:
                score_query = """
                    SELECT AVG(CAST(difficulty AS FLOAT)) as avg_score
                    FROM questions 
                    WHERE topic_tag1 = %s OR topic_tag2 = %s OR topic_tag3 = %s
                """
                cursor.execute(score_query, (topic, topic, topic))
                score_result = cursor.fetchone()
                avg_score = score_result[0] if score_result and score_result[0] else 0.0
                topic_scores.append(f"{topic}: {round(avg_score, 2)}")
            
            text = "Topics (with avg difficulty):\n" + "\n".join(topic_scores)
        
        cursor.close()
        conn.close()
        return {"content": [{"type": "text", "text": text}]}
        
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# ============================================================================
# Student Memory Tools
# ============================================================================

@tool(
    "get_skill_level_pairs",
    "Get topic-skill level pairs for a student",
    {"student_name": str, "exam_name": str}
)
async def get_skill_level_pairs(args: dict[str, Any]) -> dict[str, Any]:
    """Get skill level pairs for a student."""
    student_name = args.get("student_name", "default")
    exam_name = args.get("exam_name", "default")
    
    try:
        student_id = get_or_create_student(student_name, exam_name)
        pairs = get_skill_levels(student_id)
        
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
    {"student_name": str, "exam_name": str, "date": str}
)
async def get_topics_by_date(args: dict[str, Any]) -> dict[str, Any]:
    """Get calendar entry for a date."""
    student_name = args.get("student_name", "default")
    exam_name = args.get("exam_name", "default")
    date = args.get("date", "")
    
    try:
        student_id = get_or_create_student(student_name, exam_name)
        entry = get_calendar_entry(student_id, date)
        
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
    "Add a memory note for a student",
    {"student_name": str, "exam_name": str, "memory_entry": str}
)
async def add_memory_entry(args: dict[str, Any]) -> dict[str, Any]:
    """Add memory entry for a student."""
    student_name = args.get("student_name", "default")
    exam_name = args.get("exam_name", "default")
    memory_entry = args.get("memory_entry", "")
    
    try:
        student_id = get_or_create_student(student_name, exam_name)
        success = add_student_memory(student_id, memory_entry)
        
        text = f"Memory added: '{memory_entry}'" if success else "Failed to add memory"
        return {"content": [{"type": "text", "text": text}]}
        
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@tool(
    "update_skill_level",
    "Update or set skill level for a topic",
    {"student_name": str, "exam_name": str, "topic": str, "skill_level": int}
)
async def update_skill_level(args: dict[str, Any]) -> dict[str, Any]:
    """Update skill level for a student topic."""
    student_name = args.get("student_name", "default")
    exam_name = args.get("exam_name", "default")
    topic = args.get("topic", "")
    skill_level = args.get("skill_level", 0)
    
    try:
        student_id = get_or_create_student(student_name, exam_name)
        success = set_skill_level(student_id, topic, skill_level)
        
        text = f"Skill level updated: {topic} = {skill_level}" if success else "Failed to update"
        return {"content": [{"type": "text", "text": text}]}
        
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# ============================================================================
# Create Unified MCP Server
# ============================================================================

db_server = create_sdk_mcp_server(
    "eigen-coach-db",
    "1.0.0",
    tools=[
        # Question bank tools
        get_question_by_topic,
        get_unique_topics,
        # Student memory tools
        get_skill_level_pairs,
        get_topics_by_date,
        add_memory_entry,
        update_skill_level
    ]
)


if __name__ == "__main__":
    log.info("Starting Eigen Coach unified database MCP server")
    db_server.run()
