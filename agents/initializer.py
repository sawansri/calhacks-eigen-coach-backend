"""
Initializer agent for setting up a student's study session.
"""

from database.db_helpers import get_or_create_student, get_calendar_entry, set_calendar_entry


async def initializer_agent(student_data: dict, date: str) -> dict:
    """
    Initialize a student session by setting up the calendar entry.
    
    Args:
        student_data: Dictionary with student_name, exam_name, memory
        date: Date for the session in YYYY-MM-DD format
        
    Returns:
        Calendar entry dict with date, topics, and n_questions
    """
    try:
        student_name = student_data.get("student_name", "default")
        exam_name = student_data.get("exam_name", "default")
        
        # Get or create student
        student_id = get_or_create_student(student_name, exam_name)
        
        # Check if entry already exists
        entry = get_calendar_entry(student_id, date)
        
        if entry:
            return entry
        
        # Create default entry for today
        topics = ["general"]
        n_questions = 1
        set_calendar_entry(student_id, date, topics, n_questions)
        
        return {
            "date": date,
            "topics": topics,
            "n_questions": n_questions
        }
        
    except Exception as e:
        raise Exception(f"Initializer error: {str(e)}")