# In-memory session management for TutorChat instances

from typing import Dict
from .chatter import TutorChat

# This will store active chat sessions in memory.
# In a production environment, you might replace this with a more robust
# solution like Redis or a database-backed session store.
_active_sessions: Dict[str, TutorChat] = {}

def get_session(session_id: str) -> TutorChat | None:
    """Retrieve a chat session by its ID."""
    return _active_sessions.get(session_id)

def create_session(session_id: str, student_data: dict, question_answer: str) -> TutorChat:
    """Create a new chat session and store it."""
    if session_id in _active_sessions:
        # This case should ideally be handled by the API layer
        # to prevent overwriting an active session unintentionally.
        return _active_sessions[session_id]
    
    session = TutorChat(student_data=student_data, question_answer=question_answer)
    _active_sessions[session_id] = session
    return session

def end_session(session_id: str) -> None:
    """Remove a chat session from memory."""
    if session_id in _active_sessions:
        # Here you could also add cleanup logic for the TutorChat instance if needed
        del _active_sessions[session_id]
