"""
FastAPI endpoints for the Eigen Coach tutoring system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
from datetime import datetime
import asyncio
import json

# Agent imports
from agents.initializer import initializer_agent
from agents.questioner import question_agent
from agents.chatter import TutorChat
from agents.chat_manager import get_session, create_session, end_session
from agents.finalizer import finalizer_agent

# Database
from database.db import DatabaseManager
from database.db_helpers import get_student_name, get_exam_name, get_student_memory

# Initialize FastAPI app
app = FastAPI(
    title="Eigen Coach API",
    description="API for the Eigen Coach AI tutoring system",
    version="1.0.0"
)

# ============================================================================
# Request/Response Models
# ============================================================================

class StudentData(BaseModel):
    """Student information."""
    student_name: str
    exam_name: str
    memory: List[str] = []


class InitializerRequest(BaseModel):
    """Request to initialize a student session."""
    student_data: StudentData
    date: Optional[str] = None


class InitializerResponse(BaseModel):
    """Response from initializer agent."""
    status: str
    message: str
    calendar_entry: Optional[Dict] = None


class QuestionerRequest(BaseModel):
    """Request to select a question."""
    date: Optional[str]


class QuestionerResponse(BaseModel):
    """Response from questioner agent."""
    questions: List[Dict[str, Any]]


class ChatRequest(BaseModel):
    """Request for tutoring chat."""
    session_id: str
    user_message: str
    # question_answer is only required for the first message in a session
    question_answer: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat agent."""
    response: str


class FinalizerRequest(BaseModel):
    """Request for performance evaluation."""
    student_data: StudentData
    conversation_history: List[Dict]


class FinalizerResponse(BaseModel):
    """Response from finalizer agent."""
    score_deltas: Dict[str, int]


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


# ============================================================================
# Helper Functions
# ============================================================================

def get_student_data_from_db() -> Dict[str, Any]:
    """Retrieve student data from database."""
    return {
        "student_name": get_student_name(),
        "exam_name": get_exam_name(),
        "memory": get_student_memory()
    }


# ============================================================================
# Initializer Agent Endpoint
# ============================================================================

@app.post("/initializer", response_model=InitializerResponse)
async def initializer_endpoint(request: InitializerRequest):
    """
    Initialize a student session with calendar planning.
    
    Args:
        request: InitializerRequest with student data and optional date
        
    Returns:
        InitializerResponse with status and calendar entry
    """
    try:
        date = request.date or datetime.now().strftime('%Y-%m-%d')
        student_data = get_student_data_from_db()
        
        # Call initializer agent
        result = await initializer_agent(student_data, date)
        
        return InitializerResponse(
            status="success",
            message=f"Session initialized for {student_data.get('student_name')}",
            calendar_entry=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initializer error: {str(e)}")


# ============================================================================
# Questioner Agent Endpoint
# ============================================================================

@app.post("/questioner", response_model=QuestionerResponse)
async def questioner_endpoint(request: QuestionerRequest):
    """
    Select an appropriate question for the student.
    
    Args:
        request: QuestionerRequest with student data and optional date
        
    Returns:
        QuestionerResponse with selected question
    """
    try:
        date = request.date or datetime.now().strftime('%Y-%m-%d')
        
        # Call question agent
        result = await question_agent(date)
        
        return QuestionerResponse(
            questions=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Questioner error: {str(e)}")


# ============================================================================
# Chatter Agent Endpoint
# ============================================================================

@app.post("/chatter", response_model=ChatResponse)
async def chatter_endpoint(request: ChatRequest):
    """
    Send a message to the tutoring chatbot using a session ID.
    
    Args:
        request: ChatRequest with session_id and user_message.
                 question_answer is required to start a new session.
        
    Returns:
        ChatResponse with tutor response.
    """
    try:
        # 1. Get the chat session
        chat_session = get_session(request.session_id)

        # 2. If no session exists, create a new one
        if not chat_session:
            if not request.question_answer:
                raise HTTPException(
                    status_code=400, 
                    detail="'question_answer' is required to start a new chat session."
                )
            
            student_data = get_student_data_from_db()
            chat_session = create_session(
                session_id=request.session_id,
                student_data=student_data,
                question_answer=request.question_answer
            )

        # 3. Process the chat message
        response = await chat_session.chat(request.user_message)
        
        return ChatResponse(response=response)
    except Exception as e:
        # Clean up the session on error if it exists
        if get_session(request.session_id):
            await end_session(request.session_id)
        raise HTTPException(status_code=500, detail=f"Chatter error: {str(e)}")


# ============================================================================
# Finalizer Agent Endpoint
# ============================================================================

@app.post("/finalizer", response_model=FinalizerResponse)
async def finalizer_endpoint(request: FinalizerRequest):
    """
    Evaluate student performance and generate score deltas.
    
    Args:
        request: FinalizerRequest with student data and conversation history
        
    Returns:
        FinalizerResponse with score deltas for each topic
    """
    try:
        student_data = get_student_data_from_db()
        
        # Call finalizer agent
        result = await finalizer_agent(student_data, request.conversation_history)
        
        # Parse result if it's JSON string
        if isinstance(result, str):
            result = json.loads(result)
        
        return FinalizerResponse(score_deltas=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finalizer error: {str(e)}")
