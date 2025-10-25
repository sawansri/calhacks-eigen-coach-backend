from typing import Any, Optional
try:
    import mysql.connector  # type: ignore
    from mysql.connector import Error  # type: ignore
    MYSQL_AVAILABLE = True
except Exception:
    # mysql-connector not available; server should still start so other tools can work
    mysql = None  # type: ignore
    Error = Exception  # type: ignore
    MYSQL_AVAILABLE = False
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("question_bank")

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
        print(f"Database connection error: {e}")
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
    """Get all unique topics from the question bank with their average difficulty scores."""
    result = get_unique_topics_helper()
    
    if isinstance(result, str):
        return result
    
    # Format the list with topic-score pairs for display
    formatted_pairs = []
    for topic, score in result:
        formatted_pairs.append(f"{topic}: {score}")
    
    return "Topics with Average Scores:\n" + "\n".join(f"- {pair}" for pair in formatted_pairs)


if __name__ == "__main__":
    mcp.run()

