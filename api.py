"""
FastAPI endpoints for the Eigen Coach tutoring system.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Dict, Optional
import json
import os

from src.orchestrator_agent import OrchestratorAgent
from src.document_ingestion_agent import DocumentIngestionAgent
from src.planner_agent import PlannerAgent
from src.tutor_agent import TutorAgent
from src.feedback_agent import FeedbackAgent
from src.scraper_agent import ScraperAgent


# Initialize FastAPI app
app = FastAPI(
    title="Eigen Coach API",
    description="API for the Eigen Coach AI tutoring system",
    version="1.0.0"
)

# Initialize agents
orchestrator = OrchestratorAgent()
doc_ingestion = DocumentIngestionAgent()
planner = PlannerAgent()
tutor = TutorAgent()
feedback = FeedbackAgent()
scraper = ScraperAgent()


# ============================================================================
# In-Memory Storage for User Data
# ============================================================================

class UserData(BaseModel):
    """Request model for storing user data."""
    value: str


# In-memory variables
user_name = None
question1 = None
question2 = None
question3 = None
question4 = None
question5 = None
question6 = None
question7 = None


# ============================================================================
# User Data Endpoints
# ============================================================================

@app.post("/name")
def set_name(data: UserData):
    """
    Set the user's name in memory.
    
    Args:
        data: UserData containing the name value
        
    Returns:
        Confirmation message with the stored name
    """
    global user_name
    user_name = data.value
    return {
        "status": "success",
        "message": f"Name set to: {user_name}",
        "name": user_name
    }


@app.post("/question1")
def set_question1(data: UserData):
    """
    Set question1 in memory.
    
    Args:
        data: UserData containing the question1 value
        
    Returns:
        Confirmation message with the stored value
    """
    global question1
    question1 = data.value
    return {
        "status": "success",
        "message": f"Question1 set to: {question1}",
        "question1": question1
    }


@app.post("/question2")
def set_question2(data: UserData):
    """
    Set question2 in memory.
    
    Args:
        data: UserData containing the question2 value
        
    Returns:
        Confirmation message with the stored value
    """
    global question2
    question2 = data.value
    return {
        "status": "success",
        "message": f"Question2 set to: {question2}",
        "question2": question2
    }


@app.post("/question3")
def set_question3(data: UserData):
    """
    Set question3 in memory.
    
    Args:
        data: UserData containing the question3 value
        
    Returns:
        Confirmation message with the stored value
    """
    global question3
    question3 = data.value
    return {
        "status": "success",
        "message": f"Question3 set to: {question3}",
        "question3": question3
    }


@app.post("/question4")
def set_question4(data: UserData):
    """
    Set question4 in memory.
    
    Args:
        data: UserData containing the question4 value
        
    Returns:
        Confirmation message with the stored value
    """
    global question4
    question4 = data.value
    return {
        "status": "success",
        "message": f"Question4 set to: {question4}",
        "question4": question4
    }


@app.post("/question5")
def set_question5(data: UserData):
    """
    Set question5 in memory.
    
    Args:
        data: UserData containing the question5 value
        
    Returns:
        Confirmation message with the stored value
    """
    global question5
    question5 = data.value
    return {
        "status": "success",
        "message": f"Question5 set to: {question5}",
        "question5": question5
    }


@app.post("/question6")
def set_question6(data: UserData):
    """
    Set question6 in memory.
    
    Args:
        data: UserData containing the question6 value
        
    Returns:
        Confirmation message with the stored value
    """
    global question6
    question6 = data.value
    return {
        "status": "success",
        "message": f"Question6 set to: {question6}",
        "question6": question6
    }


@app.post("/question7")
def set_question7(data: UserData):
    """
    Set question7 in memory.
    
    Args:
        data: UserData containing the question7 value
        
    Returns:
        Confirmation message with the stored value
    """
    global question7
    question7 = data.value
    return {
        "status": "success",
        "message": f"Question7 set to: {question7}",
        "question7": question7
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
