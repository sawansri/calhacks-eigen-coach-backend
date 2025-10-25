"""Database helper functions for a single-student Eigen Coach instance."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from database.db import DatabaseManager


DEFAULT_STUDENT_NAME = os.getenv("EIGEN_STUDENT_NAME", "Eigen Student")
DEFAULT_EXAM_NAME = os.getenv("EIGEN_EXAM_NAME", "Eigen Exam")


def get_student_name() -> str:
    """Return the student name."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT student_name FROM students LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else DEFAULT_STUDENT_NAME
    finally:
        cursor.close()
        conn.close()


def get_exam_name() -> str:
    """Return the exam name."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT exam_name FROM students LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else DEFAULT_EXAM_NAME
    finally:
        cursor.close()
        conn.close()


def get_student_memory() -> List[str]:
    """Return memory entries."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT memory_entry FROM student_memory ORDER BY created_at"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def add_student_memory(memory_entry: str) -> bool:
    """Add a memory entry."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO student_memory (memory_entry) VALUES (%s)",
            (memory_entry,),
        )
        return True
    finally:
        cursor.close()
        conn.close()


def get_calendar_entry(date: str) -> Optional[Dict[str, Any]]:
    """Return the calendar entry for the given date."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT date, topics, n_questions FROM calendar_entries WHERE date = %s",
            (date,),
        )
        result = cursor.fetchone()
        if result:
            result["topics"] = json.loads(result["topics"])
        return result
    finally:
        cursor.close()
        conn.close()


def set_calendar_entry(date: str, topics: List[str], n_questions: int = 1) -> bool:
    """Create or update the calendar entry."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        topics_json = json.dumps(topics)
        cursor.execute(
            """INSERT INTO calendar_entries (date, topics, n_questions)
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE topics = %s, n_questions = %s""",
            (date, topics_json, n_questions, topics_json, n_questions),
        )
        return True
    finally:
        cursor.close()
        conn.close()


def get_skill_levels() -> List[Tuple[str, int]]:
    """Return skill levels."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT topic, skill_level FROM skill_levels ORDER BY topic"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def set_skill_level(topic: str, skill_level: int) -> bool:
    """Set the skill level for a topic."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO skill_levels (topic, skill_level)
               VALUES (%s, %s)
               ON DUPLICATE KEY UPDATE skill_level = %s""",
            (topic, skill_level, skill_level),
        )
        return True
    finally:
        cursor.close()
        conn.close()


def get_questions_by_topic(topic: str) -> List[Dict]:
    """Return all questions for a given topic."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM questions
            WHERE topic_tag1 = %s OR topic_tag2 = %s OR topic_tag3 = %s
        """
        cursor.execute(query, (topic, topic, topic))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
