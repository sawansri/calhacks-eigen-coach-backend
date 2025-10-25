"""Default data seeding utilities for the Eigen Coach database."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from mysql.connector import Error


SEEDS_DIR = Path(__file__).resolve().parent / "seeds"
STUDENTS_FILE = SEEDS_DIR / "students.json"
MEMORY_FILE = SEEDS_DIR / "student_memory.json"
CALENDAR_FILE = SEEDS_DIR / "calendar_entries.json"
SKILL_LEVELS_FILE = SEEDS_DIR / "skill_levels.json"
QUESTIONS_FILE = SEEDS_DIR / "questions.json"

DEFAULT_STUDENT_NAME = os.getenv("EIGEN_STUDENT_NAME", "Eigen Student")
DEFAULT_EXAM_NAME = os.getenv("EIGEN_EXAM_NAME", "Eigen Exam")


def _load_json(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _table_is_empty(conn, table_name: str) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count_row = cursor.fetchone()
        return count_row[0] == 0 if count_row else True
    finally:
        cursor.close()


def _get_or_create_student_id(
    conn,
    student_name: Optional[str] = None,
    exam_name: Optional[str] = None,
) -> int:
    cursor = conn.cursor()
    try:
        name = student_name or DEFAULT_STUDENT_NAME
        exam = exam_name or DEFAULT_EXAM_NAME

        cursor.execute(
            "SELECT id, student_name, exam_name FROM students ORDER BY id LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            if row[1] != name or row[2] != exam:
                cursor.execute(
                    "UPDATE students SET student_name = %s, exam_name = %s WHERE id = %s",
                    (name, exam, row[0]),
                )
            return row[0]

        cursor.execute(
            "INSERT INTO students (student_name, exam_name) VALUES (%s, %s)",
            (name, exam),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def _seed_students(conn) -> None:
    students = _load_json(STUDENTS_FILE)
    first = students[0] if students else {}
    student_id = _get_or_create_student_id(
        conn,
        first.get("student_name") if isinstance(first, dict) else None,
        first.get("exam_name") if isinstance(first, dict) else None,
    )
    print(f"[DatabaseSeeder] Ensured single student record (id={student_id})")


def _seed_student_memory(conn) -> None:
    memory_entries = _load_json(MEMORY_FILE)
    if not memory_entries:
        return

    try:
        if not _table_is_empty(conn, "student_memory"):
            print("[DatabaseSeeder] Skipping student memory seed; table already populated")
            return
    except Error as exc:
        print(f"[DatabaseSeeder] Unable to inspect student_memory table: {exc}")
        return

    insert_sql = "INSERT INTO student_memory (student_id, memory_entry) VALUES (%s, %s)"

    student_id = _get_or_create_student_id(conn)
    cursor = conn.cursor()
    try:
        for entry in memory_entries:
            memory_text = (
                entry.get("memory_entry")
                if isinstance(entry, dict)
                else entry
            )
            if not memory_text:
                continue
            cursor.execute(insert_sql, (student_id, memory_text))
        conn.commit()
        print(f"[DatabaseSeeder] Seeded {len(memory_entries)} student memory entries")
    except Error as exc:
        print(f"[DatabaseSeeder] Failed to seed student memory: {exc}")
    finally:
        cursor.close()


def _seed_calendar_entries(conn) -> None:
    entries = _load_json(CALENDAR_FILE)
    if not entries:
        return

    try:
        if not _table_is_empty(conn, "calendar_entries"):
            print("[DatabaseSeeder] Skipping calendar entries seed; table already populated")
            return
    except Error as exc:
        print(f"[DatabaseSeeder] Unable to inspect calendar_entries table: {exc}")
        return

    insert_sql = (
        "INSERT INTO calendar_entries (student_id, date, topics, n_questions) "
        "VALUES (%s, %s, %s, %s)"
    )

    student_id = _get_or_create_student_id(conn)
    cursor = conn.cursor()
    try:
        for entry in entries:
            date = entry.get("date")
            if not date:
                continue
            topics_json = json.dumps(entry.get("topics", []))
            cursor.execute(
                insert_sql,
                (
                    student_id,
                    date,
                    topics_json,
                    entry.get("n_questions", 1),
                ),
            )
        conn.commit()
        print(f"[DatabaseSeeder] Seeded {len(entries)} calendar entries")
    except Error as exc:
        print(f"[DatabaseSeeder] Failed to seed calendar entries: {exc}")
    finally:
        cursor.close()


def _seed_skill_levels(conn) -> None:
    skills = _load_json(SKILL_LEVELS_FILE)
    if not skills:
        return

    try:
        if not _table_is_empty(conn, "skill_levels"):
            print("[DatabaseSeeder] Skipping skill levels seed; table already populated")
            return
    except Error as exc:
        print(f"[DatabaseSeeder] Unable to inspect skill_levels table: {exc}")
        return

    insert_sql = "INSERT INTO skill_levels (student_id, topic, skill_level) VALUES (%s, %s, %s)"

    student_id = _get_or_create_student_id(conn)
    cursor = conn.cursor()
    try:
        for entry in skills:
            topic = entry.get("topic") if isinstance(entry, dict) else None
            if not topic:
                continue
            cursor.execute(
                insert_sql,
                (student_id, topic, entry.get("skill_level", 0)),
            )
        conn.commit()
        print(f"[DatabaseSeeder] Seeded {len(skills)} skill level rows")
    except Error as exc:
        print(f"[DatabaseSeeder] Failed to seed skill levels: {exc}")
    finally:
        cursor.close()


def _seed_questions(conn) -> None:
    questions = _load_json(QUESTIONS_FILE)
    if not questions:
        return

    try:
        if not _table_is_empty(conn, "questions"):
            print("[DatabaseSeeder] Skipping questions seed; table already populated")
            return
    except Error as exc:
        print(f"[DatabaseSeeder] Unable to inspect questions table: {exc}")
        return

    insert_sql = (
        "INSERT INTO questions (question_prompt, answer, explanation, difficulty, "
        "topic_tag1, topic_tag2, topic_tag3, has_been_asked) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )

    cursor = conn.cursor()
    try:
        for entry in questions:
            payload = (
                entry.get("question_prompt"),
                entry.get("answer"),
                entry.get("explanation"),
                entry.get("difficulty", "medium"),
                entry.get("topic_tag1"),
                entry.get("topic_tag2"),
                entry.get("topic_tag3"),
                1 if entry.get("has_been_asked") else 0,
            )
            cursor.execute(insert_sql, payload)
        conn.commit()
        print(f"[DatabaseSeeder] Seeded {len(questions)} default questions")
    except Error as exc:
        print(f"[DatabaseSeeder] Failed to seed questions: {exc}")
    finally:
        cursor.close()


def run_seeders(conn) -> None:
    """Run all available default data seeders."""
    try:
        _seed_students(conn)
        _seed_student_memory(conn)
        _seed_calendar_entries(conn)
        _seed_skill_levels(conn)
        _seed_questions(conn)
    except Error as exc:
        print(f"[DatabaseSeeder] Error during seeding: {exc}")