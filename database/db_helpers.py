"""
Database helper functions for student data operations.
"""

from database.db import DatabaseManager
from typing import Optional, List, Dict, Tuple
import json


def get_or_create_student(student_name: str, exam_name: str) -> int:
    """Get student ID or create new student record.
    
    Args:
        student_name: Name of the student
        exam_name: Name of the exam
        
    Returns:
        Student ID
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Try to find existing student
        cursor.execute(
            "SELECT id FROM students WHERE student_name = %s AND exam_name = %s",
            (student_name, exam_name)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new student
        cursor.execute(
            "INSERT INTO students (student_name, exam_name) VALUES (%s, %s)",
            (student_name, exam_name)
        )
        return cursor.lastrowid
        
    finally:
        cursor.close()
        conn.close()


def get_student_memory(student_id: int) -> List[str]:
    """Get all memory entries for a student.
    
    Args:
        student_id: Student ID
        
    Returns:
        List of memory entry strings
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT memory_entry FROM student_memory WHERE student_id = %s ORDER BY created_at",
            (student_id,)
        )
        return [row[0] for row in cursor.fetchall()]
        
    finally:
        cursor.close()
        conn.close()


def add_student_memory(student_id: int, memory_entry: str) -> bool:
    """Add a memory entry for a student.
    
    Args:
        student_id: Student ID
        memory_entry: Memory text to add
        
    Returns:
        True if successful
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO student_memory (student_id, memory_entry) VALUES (%s, %s)",
            (student_id, memory_entry)
        )
        return True
        
    finally:
        cursor.close()
        conn.close()


def get_calendar_entry(student_id: int, date: str) -> Optional[Dict]:
    """Get calendar entry for a specific date.
    
    Args:
        student_id: Student ID
        date: Date string (YYYY-MM-DD)
        
    Returns:
        Dict with date, topics, n_questions or None
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT date, topics, n_questions FROM calendar_entries WHERE student_id = %s AND date = %s",
            (student_id, date)
        )
        result = cursor.fetchone()
        
        if result:
            result['topics'] = json.loads(result['topics'])
        
        return result
        
    finally:
        cursor.close()
        conn.close()


def set_calendar_entry(student_id: int, date: str, topics: List[str], n_questions: int = 1) -> bool:
    """Set or update calendar entry for a date.
    
    Args:
        student_id: Student ID
        date: Date string (YYYY-MM-DD)
        topics: List of topic strings
        n_questions: Number of questions
        
    Returns:
        True if successful
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    try:
        topics_json = json.dumps(topics)
        cursor.execute(
            """INSERT INTO calendar_entries (student_id, date, topics, n_questions) 
               VALUES (%s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE topics = %s, n_questions = %s""",
            (student_id, date, topics_json, n_questions, topics_json, n_questions)
        )
        return True
        
    finally:
        cursor.close()
        conn.close()


def get_skill_levels(student_id: int) -> List[Tuple[str, int]]:
    """Get all skill levels for a student.
    
    Args:
        student_id: Student ID
        
    Returns:
        List of (topic, skill_level) tuples
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT topic, skill_level FROM skill_levels WHERE student_id = %s ORDER BY topic",
            (student_id,)
        )
        return cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()


def set_skill_level(student_id: int, topic: str, skill_level: int) -> bool:
    """Set or update skill level for a topic.
    
    Args:
        student_id: Student ID
        topic: Topic name
        skill_level: Skill level (0-100)
        
    Returns:
        True if successful
    """
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO skill_levels (student_id, topic, skill_level) 
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE skill_level = %s""",
            (student_id, topic, skill_level, skill_level)
        )
        return True
        
    finally:
        cursor.close()
        conn.close()
