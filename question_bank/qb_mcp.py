from typing import Any, Optional
import sys
import os
import logging
import json

# Configure logging
log = logging.getLogger("question_bank_mcp")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

from claude_agent_sdk import tool, create_sdk_mcp_server

try:
    import mysql.connector  # type: ignore
    from mysql.connector import Error  # type: ignore
    MYSQL_AVAILABLE = True
except Exception:
    # mysql-connector not available; server should still start so other tools can work
    mysql = None  # type: ignore
    Error = Exception  # type: ignore
    MYSQL_AVAILABLE = False

# Helpers
def get_db_connection():
    """Create and return a MySQL database connection"""
    if not MYSQL_AVAILABLE:
        return None
    try:
        connection = mysql.connector.connect(  # type: ignore
            host='localhost',
            port=8003,
            user='root',
            password='joe_is_very_cool',
            database='calhacks'
        )
        return connection
    except Error as e:  # type: ignore
        log.error(f"Database connection error: {e}")
        return None

def get_unique_topics_helper() -> list | str:
    """Helper method to get all unique topics with their current scores from the question bank.
    
    Returns:
        List of tuples with (topic, average_score), or error message string
    """
    connection = get_db_connection()
    if not connection:
        if not MYSQL_AVAILABLE:
            return "mysql-connector not installed; question_bank MCP unavailable."
        return "Unable to connect to database."
    
    try:
        cursor = connection.cursor()
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
            return "No topics found in database."
        
        topics = [row[0] for row in topics_results if row[0]]
        topic_scores = []
        
        # For each topic, calculate average score
        for topic in topics:
            score_query = """
            SELECT AVG(CAST(difficulty AS FLOAT)) as avg_score
            FROM questions 
            WHERE topic_tag1 = %s OR topic_tag2 = %s OR topic_tag3 = %s
            """
            cursor.execute(score_query, (topic, topic, topic))
            score_result = cursor.fetchone()
            avg_score = score_result[0] if score_result and score_result[0] else 0.0
            topic_scores.append((topic, round(avg_score, 2)))
        
        return topic_scores
    
    except Error as e:
        return f"Database query error: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@tool("get_question_by_topic", "Get questions from the database by topic tag", {"topic": str})
async def get_question_by_topic(args: dict[str, Any]) -> dict[str, Any]:
    """Get questions from the database by topic tag.

    Args:
        topic: Topic tag to search for (topic_tag1, topic_tag2, or topic_tag3)
    """
    topic = args.get("topic", "")
    
    connection = get_db_connection()
    if not connection:
        text = "Unable to connect to database."
        return {
            "content": [{
                "type": "text",
                "text": text
            }]
        }
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM questions WHERE topic_tag1 = %s OR topic_tag2 = %s OR topic_tag3 = %s"
        cursor.execute(query, (topic, topic, topic))
        results = cursor.fetchall()
        
        if not results:
            text = f"No questions found for topic: {topic}"
        else:
            formatted_results = []
            for row in results:
                formatted = f"""
                Question: {row['question_prompt']}
                Answer: {row['answer']}
                Explanation: {row['explanation']}
                Difficulty: {row['difficulty']}
                Topic Tags: {row['topic_tag1']}, {row['topic_tag2']}, {row['topic_tag3']}
                Has Been Asked: {row['has_been_asked']}
                ---"""
                formatted_results.append(formatted)
            
            text = "\n".join(formatted_results)
    
    except Error as e:
        text = f"Database query error: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return {
        "content": [{
            "type": "text",
            "text": text
        }]
    }

@tool("get_unique_topics", "Get all unique topics from the question bank with their average difficulty scores", {})
async def get_unique_topics(args: dict[str, Any]) -> dict[str, Any]:
    """Get all unique topics from the question bank with their average difficulty scores."""
    result = get_unique_topics_helper()
    
    if isinstance(result, str):
        text = result
    else:
        # Format the list with topic-score pairs for display
        formatted_pairs = []
        for topic, score in result:
            formatted_pairs.append(f"{topic}: {score}")
        
        text = "Topics with Average Scores:\n" + "\n".join(f"- {pair}" for pair in formatted_pairs)
    
    return {
        "content": [{
            "type": "text",
            "text": text
        }]
    }


# Create the SDK MCP server with all tools
qb_server = create_sdk_mcp_server(
    name="question-bank",
    version="1.0.0",
    tools=[
        get_question_by_topic,
        get_unique_topics
    ]
)


if __name__ == "__main__":
    try:
        log.info("Starting Question Bank MCP Server...")
        log.info(f"Working directory = {os.getcwd()}")
        log.info(f"MySQL available = {MYSQL_AVAILABLE}")
        
        if MYSQL_AVAILABLE:
            # Try to connect to verify MySQL is working
            conn = get_db_connection()
            if conn:
                log.info("Successfully connected to MySQL database")
                conn.close()
            else:
                log.warning("Failed to connect to MySQL database")
        else:
            log.warning("MySQL not available - MCP will run in degraded mode")
        
        log.info("Starting qb_server...")
        qb_server.run()
        log.info("qb_server completed")
        
    except KeyboardInterrupt:
        log.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        log.error(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

