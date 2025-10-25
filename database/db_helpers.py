"""Database helper functions for a single-student Eigen Coach instance."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from database.db import DatabaseManager


DEFAULT_STUDENT_NAME = os.getenv("EIGEN_STUDENT_NAME", "Eigen Student")
DEFAULT_EXAM_NAME = os.getenv("EIGEN_EXAM_NAME", "Eigen Exam")


def get_or_create_student(student_name: Optional[str] = None, exam_name: Optional[str] = None) -> int:
    """Return the single student ID, creating or updating it as needed."""
    name = student_name or DEFAULT_STUDENT_NAME
    exam = exam_name or DEFAULT_EXAM_NAME

    conn = DatabaseManager.get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, student_name, exam_name FROM students ORDER BY id LIMIT 1")
        record = cursor.fetchone()

        if record:
            if record["student_name"] != name or record["exam_name"] != exam:
                cursor.execute(
                    "UPDATE students SET student_name = %s, exam_name = %s WHERE id = %s",
                    (name, exam, record["id"]),
                )
            return record["id"]

        cursor.execute(
            "INSERT INTO students (student_name, exam_name) VALUES (%s, %s)",
            (name, exam),
        )
        return cursor.lastrowid

    finally:
        cursor.close()
        conn.close()


def get_student_profile() -> Dict[str, str]:
    """Return the stored student profile."""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT student_name, exam_name FROM students ORDER BY id LIMIT 1")
        record = cursor.fetchone()
        if record:
            return {
                "student_name": record["student_name"],
                "exam_name": record["exam_name"],
            }
        return {"student_name": DEFAULT_STUDENT_NAME, "exam_name": DEFAULT_EXAM_NAME}
    finally:
        cursor.close()
        conn.close()


def get_student_memory() -> List[str]:
    """Return memory entries for the single student."""
    student_id = get_or_create_student()
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT memory_entry FROM student_memory WHERE student_id = %s ORDER BY created_at",
            (student_id,),
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def add_student_memory(memory_entry: str) -> bool:
    """Add a memory entry for the single student."""
    student_id = get_or_create_student()
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO student_memory (student_id, memory_entry) VALUES (%s, %s)",
            (student_id, memory_entry),
        )
        return True
    finally:
        cursor.close()
        conn.close()


def get_calendar_entry(date: str) -> Optional[Dict[str, Any]]:
    """Return the calendar entry for the single student on the given date."""
    student_id = get_or_create_student()
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT date, topics, n_questions FROM calendar_entries WHERE student_id = %s AND date = %s",
            (student_id, date),
        )
        result = cursor.fetchone()
        if result:
            result["topics"] = json.loads(result["topics"])
        return result
    finally:
        cursor.close()
        conn.close()


def set_calendar_entry(date: str, topics: List[str], n_questions: int = 1) -> bool:
    """Create or update the calendar entry for the single student."""
    student_id = get_or_create_student()
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        topics_json = json.dumps(topics)
        cursor.execute(
            """INSERT INTO calendar_entries (student_id, date, topics, n_questions)
               VALUES (%s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE topics = %s, n_questions = %s""",
            (student_id, date, topics_json, n_questions, topics_json, n_questions),
        )
        return True
    finally:
        cursor.close()
        conn.close()


def get_skill_levels() -> List[Tuple[str, int]]:
    """Return skill levels for the single student."""
    student_id = get_or_create_student()
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT topic, skill_level FROM skill_levels WHERE student_id = %s ORDER BY topic",
            (student_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def set_skill_level(topic: str, skill_level: int) -> bool:
    """Set the skill level for a topic for the single student."""
    student_id = get_or_create_student()
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO skill_levels (student_id, topic, skill_level)
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE skill_level = %s""",
            (student_id, topic, skill_level, skill_level),
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
