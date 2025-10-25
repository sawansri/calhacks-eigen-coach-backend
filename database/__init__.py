"""
Eigen Coach unified database package.
"""

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

__all__ = [
    'DatabaseManager',
    'get_or_create_student',
    'get_student_memory',
    'add_student_memory',
    'get_calendar_entry',
    'set_calendar_entry',
    'get_skill_levels',
    'set_skill_level'
]
