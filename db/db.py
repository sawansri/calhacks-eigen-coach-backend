import mysql.connector
from mysql.connector import Error

def initialize_database():
    """Initialize MySQL database and create questions table"""
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            port=8003,
            user='root',
            password='joe_is_very_cool' 
        )
        
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS calhacks")
        cursor.execute("USE calhacks")
        
        # Create questions table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question_prompt TEXT NOT NULL,
            answer TEXT NOT NULL,
            explanation TEXT,
            topic_tag1 VARCHAR(100),
            topic_tag2 VARCHAR(100),
            topic_tag3 VARCHAR(100),
            difficulty VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        cursor.execute(create_table_query)
        connection.commit()
        print("Database initialized successfully!")
        
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    initialize_database()
