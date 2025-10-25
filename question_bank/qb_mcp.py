from typing import Any
import httpx
import mysql.connector
from mysql.connector import Error
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("question_bank")

# Helpers
def get_db_connection():
    """Create and return a MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=8003,
            user='root',
            password='joe_is_very_cool',
            database='calhacks'
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

@mcp.tool()
async def get_question_by_topic(topic: str) -> str:
    """Get questions from the database by topic tag.

    Args:
        topic: Topic tag to search for (topic_tag1, topic_tag2, or topic_tag3)
    """
    connection = get_db_connection()
    if not connection:
        return "Unable to connect to database."
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM questions WHERE topic_tag1 = %s OR topic_tag2 = %s OR topic_tag3 = %s"
        cursor.execute(query, (topic, topic, topic))
        results = cursor.fetchall()
        
        if not results:
            return f"No questions found for topic: {topic}"
        
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
        
        return "\n".join(formatted_results)
    
    except Error as e:
        return f"Database query error: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@mcp.tool()
async def get_unique_topics() -> str:
    """Get all unique topics from the question bank."""
    connection = get_db_connection()
    if not connection:
        return "Unable to connect to database."
    
    try:
        cursor = connection.cursor()
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
        results = cursor.fetchall()
        
        if not results:
            return "No topics found in database."
        
        topics = [row[0] for row in results if row[0]]
        return f"Unique topics:\n" + "\n".join(f"- {topic}" for topic in topics)
    
    except Error as e:
        return f"Database query error: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    mcp.run()

