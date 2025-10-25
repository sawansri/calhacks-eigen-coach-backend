import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from memory.memory import get_db
from agents.questioner import question_agent
from agents.chatter import TutorChat
from agents.finalizer import finalizer_agent


class Orchestrator:
    """Minimal orchestrator that deterministically routes tasks to the right agent.
    
    This is a lightweight, reliable implementation designed for hackathon speed.
    It can be swapped later for an LLM-driven agent if adaptive reasoning is desired.
    """

    async def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route based on the provided stage and available context.
        
        Expected payload keys (all optional, depending on stage):
        - stage: one of [init, planned, asked, chatted]
        - date: ISO date string; defaults to today
        - student_data: dict for chat/finalize
        - message: user message for chat
        - conversation_history: list of {role, content} for finalize
        
        Returns a dict with at least {"action": str, ...} and any agent results.
        """
        stage = (payload.get("stage") or "").lower()
        date = payload.get("date") or datetime.now().strftime('%Y-%m-%d')

        if stage == "init":
            return await self._stage_init(date)

        if stage == "planned":
            return await self._stage_planned(date)

        if stage == "asked":
            return await self._stage_asked(payload)

        if stage == "chatted":
            return await self._stage_chatted(payload)

        # Unknown stage -> suggest planning
        return {
            "action": "seed_calendar",
            "reason": "Unknown stage; suggest seeding today's schedule.",
            "example_body": {
                "entries": [
                    {"date": date, "topics": ["algebra"], "n_questions": 1}
                ]
            }
        }

    async def _stage_init(self, date: str) -> Dict[str, Any]:
        try:
            db = get_db("calendar")
            has_date = any((r.get("date") == date) for r in db.all())
        except Exception:
            has_date = False
        if not has_date:
            return {
                "action": "seed_calendar",
                "reason": "No schedule found for date; seed calendar first.",
                "example_body": {
                    "entries": [
                        {"date": date, "topics": ["algebra"], "n_questions": 1}
                    ]
                }
            }
        # If schedule exists, select a question
        return await self._select_question(date)

    async def _stage_planned(self, date: str) -> Dict[str, Any]:
        return await self._select_question(date)

    async def _stage_asked(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        student_data = payload.get("student_data") or {}
        message = payload.get("message") or ""
        tutor = TutorChat(student_data)
        text = await tutor.chat(message)
        await tutor.close()
        return {
            "action": "chat",
            "response": text or ""
        }

    async def _stage_chatted(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        student_data = payload.get("student_data") or {}
        history = payload.get("conversation_history") or []
        deltas = await finalizer_agent(student_data, history)
        # Persist to TinyDB skill levels (best-effort)
        try:
            db = get_db("skill_level")
            if isinstance(deltas, dict):
                for topic, score in deltas.items():
                    db.insert({"topic": topic, "skill_level": score})
        except Exception:
            pass
        return {
            "action": "finalize",
            "deltas": deltas if isinstance(deltas, dict) else {"raw": deltas}
        }

    async def _select_question(self, date: str) -> Dict[str, Any]:
        raw = await question_agent(date)
        result: Dict[str, Any] = {"action": "select_question", "raw": raw}
        if raw and "Selected Question:" in raw and "|" in raw:
            parsed: Dict[str, Any] = {}
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
            result.update(parsed)
        return result
