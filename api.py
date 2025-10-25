"""
FastAPI endpoints for the Eigen Coach tutoring system.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
import json
import os
from datetime import datetime

# Agent imports
from agents.questioner import question_agent
from agents.chatter import TutorChat
from agents.finalizer import finalizer_agent
from agents.orchestrator import Orchestrator

# TinyDB helpers for calendar/skills persistence
from memory.memory import get_db

# Initialize FastAPI app
app = FastAPI(
    title="Eigen Coach API",
    description="API for the Eigen Coach AI tutoring system",
    version="1.0.0"
)

# ============================================================================
# In-Memory Storage for User Data
# ============================================================================

class UserData(BaseModel):
    """Request model for storing user data."""
    value: str


# ----------------------------------------------------------------------------
# Minimal models for new endpoints
# ----------------------------------------------------------------------------

class CalendarEntry(BaseModel):
    date: str
    topics: List[str]
    n_questions: int = 1

class CalendarSeedRequest(BaseModel):
    entries: List[CalendarEntry]

class QuestionSelectResponse(BaseModel):
    question: str
    answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    topic_tags: Optional[List[str]] = None

class ChatRequest(BaseModel):
    student_data: Dict
    message: str

class ChatResponse(BaseModel):
    response: str

class FinalizeRequest(BaseModel):
    student_data: Dict
    conversation_history: List[Dict]

class FinalizeResponse(BaseModel):
    deltas: Dict[str, int] | Dict

class SessionNextRequest(BaseModel):
    stage: str  # one of: init, planned, asked, chatted
    date: Optional[str] = None

class SessionNextResponse(BaseModel):
    next: Dict[str, str]

class OrchestrateRequest(BaseModel):
    payload: Dict[str, Any]

class OrchestrateResponse(BaseModel):
    result: Dict[str, Any]


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


# ============================================================================
# Minimal working endpoints to call agents directly
# ============================================================================

@app.post("/calendar/seed")
def seed_calendar(req: CalendarSeedRequest):
    """Seed TinyDB calendar with provided entries."""
    try:
        db = get_db("calendar")
        for e in req.entries:
            db.insert({
                "date": e.date,
                "topics": e.topics,
                "n_questions": e.n_questions,
            })
        return {"status": "ok", "inserted": len(req.entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/topics")
def get_topics(date: str):
    """Get topics and n_questions for a specific date from TinyDB calendar."""
    try:
        db = get_db("calendar")
        records = db.all()
        for r in records:
            if r.get("date") == date:
                return {
                    "date": date,
                    "topics": r.get("topics", []),
                    "n_questions": r.get("n_questions", 0)
                }
        raise HTTPException(status_code=404, detail=f"No schedule found for {date}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/question/select", response_model=QuestionSelectResponse)
async def select_question(date: Optional[str] = None):
    """Use the questioner agent to select a question for the given date (defaults to today)."""
    try:
        current_date = date or datetime.now().strftime('%Y-%m-%d')
        raw = await question_agent(current_date)
        if not raw:
            raise HTTPException(status_code=500, detail="Question agent returned no content")

        # Parse the pipe-delimited format if present
        # Format: "Selected Question: {q} | Answer: {a} | Explanation: {e} | Difficulty: {d} | Topic Tags: {tags}"
        parsed = {"question": raw}
        if "Selected Question:" in raw and "|" in raw:
            parts = [p.strip() for p in raw.split("|")]
            for p in parts:
                if ":" in p:
                    key, val = p.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key.startswith("selected question"):
                        parsed["question"] = val
                    elif key == "answer":
                        parsed["answer"] = val
                    elif key == "explanation":
                        parsed["explanation"] = val
                    elif key == "difficulty":
                        parsed["difficulty"] = val
                    elif key.startswith("topic tags"):
                        parsed["topic_tags"] = [t.strip() for t in val.split(",") if t.strip()]
        return QuestionSelectResponse(**parsed)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the TutorChat agent and return the model response."""
    try:
        tutor = TutorChat(req.student_data)
        text = await tutor.chat(req.message)
        await tutor.close()
        return ChatResponse(response=text or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session/finalize", response_model=FinalizeResponse)
async def finalize(req: FinalizeRequest):
    """Run finalizer agent and persist/update skill levels into TinyDB."""
    try:
        deltas = await finalizer_agent(req.student_data, req.conversation_history)
        # Persist to TinyDB skill_level
        try:
            db = get_db("skill_level")
            if isinstance(deltas, dict):
                for topic, score in deltas.items():
                    db.insert({"topic": topic, "skill_level": score})
        except Exception as persist_err:
            # Non-fatal persistence error; return deltas anyway
            print(f"Skill level persistence error: {persist_err}")
        return FinalizeResponse(deltas=deltas if isinstance(deltas, dict) else {"raw": deltas})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session/next", response_model=SessionNextResponse)
def session_next(req: SessionNextRequest):
    """Suggest the next API call for the frontend based on a simple session stage.

    Stages:
    - init: no plan yet; check calendar; if missing, suggest seeding; else select question
    - planned: calendar exists; select question
    - asked: question provided; start/continue chat
    - chatted: ready to finalize session
    """
    try:
        stage = (req.stage or "").lower()
        date = req.date or datetime.now().strftime('%Y-%m-%d')

        if stage == "init":
            # Check if calendar has this date
            try:
                db = get_db("calendar")
                has_date = any((r.get("date") == date) for r in db.all())
            except Exception:
                has_date = False
            if not has_date:
                example = {
                    "entries": [
                        {"date": date, "topics": ["algebra"], "n_questions": 1}
                    ]
                }
                return SessionNextResponse(next={
                    "method": "POST",
                    "endpoint": "/calendar/seed",
                    "description": "Seed today's study topics to enable question selection.",
                    "example_body": json.dumps(example)
                })
            # Calendar exists: suggest selecting a question
            return SessionNextResponse(next={
                "method": "GET",
                "endpoint": f"/question/select?date={date}",
                "description": "Select a question for today based on the calendar.",
            })

        if stage == "planned":
            return SessionNextResponse(next={
                "method": "GET",
                "endpoint": f"/question/select?date={date}",
                "description": "Select a question for the planned date.",
            })

        if stage == "asked":
            example = {
                "student_data": {"exam_name": "Exam", "student_name": "Student", "memory": []},
                "message": "My attempt is ..."
            }
            return SessionNextResponse(next={
                "method": "POST",
                "endpoint": "/chat",
                "description": "Send the student's message to the tutor agent.",
                "example_body": json.dumps(example)
            })

        if stage == "chatted":
            example = {
                "student_data": {"exam_name": "Exam", "student_name": "Student", "memory": []},
                "conversation_history": [
                    {"role": "user", "content": "my answer is ..."},
                    {"role": "assistant", "content": "..."}
                ]
            }
            return SessionNextResponse(next={
                "method": "POST",
                "endpoint": "/session/finalize",
                "description": "Finalize the session and persist skill deltas.",
                "example_body": json.dumps(example)
            })

        # Fallback: suggest planning
        example = {
            "entries": [
                {"date": date, "topics": ["algebra"], "n_questions": 1}
            ]
        }
        return SessionNextResponse(next={
            "method": "POST",
            "endpoint": "/calendar/seed",
            "description": "Unknown stage; seed the calendar to start.",
            "example_body": json.dumps(example)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
