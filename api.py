"""
FastAPI endpoints for the Eigen Coach tutoring system.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
from datetime import datetime
import asyncio
import json

# Agent imports
from agents.initializer import initializer_agent
from agents.questioner import question_agent
from agents.chatter import TutorChat
from agents.finalizer import finalizer_agent

# Database
from database.db import DatabaseManager

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
    student_data: StudentData
    date: Optional[str] = None


class QuestionerResponse(BaseModel):
    """Response from questioner agent."""
    questions: List[Dict[str, Any]]


class ChatRequest(BaseModel):
    """Request for tutoring chat."""
    student_data: StudentData
    user_message: str
    conversation_history: List[Dict] = []


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
        student_data = request.student_data.dict()
        
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
        student_data = request.student_data.dict()
        
        # Call question agent
        result = await question_agent(student_data, date)
        
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
    Send a message to the tutoring chatbot.
    
    Args:
        request: ChatRequest with student data and user message
        
    Returns:
        ChatResponse with tutor response
    """
    try:
        student_data = request.student_data.dict()
        
        # Create or get chat session
        chat = TutorChat(student_data)
        response = await chat.chat(request.user_message)
        
        return ChatResponse(response=response)
    except Exception as e:
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
        student_data = request.student_data.dict()
        
        # Call finalizer agent
        result = await finalizer_agent(student_data, request.conversation_history)
        
        # Parse result if it's JSON string
        if isinstance(result, str):
            result = json.loads(result)
        
        return FinalizerResponse(score_deltas=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finalizer error: {str(e)}")
