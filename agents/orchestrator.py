import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from memory.memory import get_db
from agents.questioner import question_agent
from agents.chatter import TutorChat
from agents.finalizer import finalizer_agent


class Orchestrator:
    """Deterministic orchestrator that routes tasks and keeps session history.

    - Logs every orchestration decision and agent call into TinyDB (db name: orchestrator)
    - If no stage is provided, infers it from calendar + recent history
    - Optional auto-execution to perform the next step instead of suggest-only
    """

    async def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route based on stage or inferred stage; log actions; optionally auto-execute.

        Payload (optional fields):
        - stage: one of [init, planned, asked, chatted]
        - date: ISO date string; defaults to today
        - student_data: dict for chat/finalize (may include student_name)
        - message: user message for chat
        - conversation_history: list of {role, content} for finalize
        - session_id: optional explicit session identifier
        - auto: bool to auto-execute next action instead of suggest-only (default False)
        - entries: optional calendar entries to seed when auto-executing init
        """
        date = payload.get("date") or datetime.now().strftime('%Y-%m-%d')
        student_data = payload.get("student_data") or {}
        session_id = payload.get("session_id") or self._derive_session_id(student_data, date)
        auto = bool(payload.get("auto", False))

        # Determine stage: use provided or infer from history + calendar
        stage = (payload.get("stage") or "").lower().strip()
        if not stage:
            stage = self._infer_stage(date=date, session_id=session_id)

        self._log(session_id, date, "orchestrate_request", {
            "stage": stage, "auto": auto, "keys": list(payload.keys())
        })

        if stage == "init":
            result = await self._stage_init(date, auto=auto, entries=payload.get("entries"))
        elif stage == "planned":
            result = await self._stage_planned(date)
        elif stage == "asked":
            result = await self._stage_asked(payload)
        elif stage == "chatted":
            result = await self._stage_chatted(payload)
        else:
            result = {
                "action": "seed_calendar",
                "reason": "Unknown stage; suggest seeding today's schedule.",
                "example_body": {
                    "entries": [
                        {"date": date, "topics": ["algebra"], "n_questions": 1}
                    ]
                }
            }

        # Log outcome
        self._log(session_id, date, "orchestrate_result", result)
        return result

    async def _stage_init(self, date: str, auto: bool = False, entries: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        try:
            db = get_db("calendar")
            has_date = any((r.get("date") == date) for r in db.all())
        except Exception:
            has_date = False
        if not has_date:
            if auto and entries:
                try:
                    for e in entries:
                        db.insert({
                            "date": e.get("date", date),
                            "topics": e.get("topics", ["algebra"]),
                            "n_questions": e.get("n_questions", 1),
                        })
                    # After seeding, immediately select question
                    seeded = {"action": "seed_calendar", "inserted": len(entries)}
                    select_res = await self._select_question(date)
                    return {"auto": True, "seed": seeded, **select_res}
                except Exception as se:
                    return {
                        "action": "seed_calendar",
                        "reason": f"Seeding failed: {se}",
                        "example_body": {"entries": entries or [{"date": date, "topics": ["algebra"], "n_questions": 1}]}
                    }
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

    # ------------------------------
    # Helpers: session, history, logs
    # ------------------------------
    def _derive_session_id(self, student_data: Dict[str, Any], date: str) -> str:
        name = (student_data.get("student_name") or "anon").strip() or "anon"
        return f"{name}:{date}"

    def _log(self, session_id: str, date: str, action: str, meta: Dict[str, Any]):
        try:
            db = get_db("orchestrator")
            db.insert({
                "ts": int(time.time()),
                "session_id": session_id,
                "date": date,
                "action": action,
                "meta": meta,
            })
        except Exception:
            # Best-effort logging
            pass

    def _get_history(self, session_id: str) -> List[Dict[str, Any]]:
        try:
            db = get_db("orchestrator")
            return sorted(db.all(), key=lambda r: r.get("ts", 0))
        except Exception:
            return []

    def _infer_stage(self, date: str, session_id: str) -> str:
        """Simple heuristic:
        - If no calendar for date -> init
        - Else if no select_question action recorded today -> planned
        - Else if there is a select_question but no chat yet -> asked
        - Else if there is at least one chat and no finalize -> chatted
        - Else fallback to planned
        """
        try:
            # calendar presence
            cal_db = get_db("calendar")
            has_date = any((r.get("date") == date) for r in cal_db.all())
        except Exception:
            has_date = False

        if not has_date:
            return "init"

        # analyze history (only for this session and date)
        history = [h for h in self._get_history(session_id) if h.get("date") == date]
        has_select = any(h.get("action") == "orchestrate_result" and (h.get("meta") or {}).get("action") == "select_question" for h in history)
        has_chat = any(h.get("action") == "orchestrate_result" and (h.get("meta") or {}).get("action") == "chat" for h in history)
        has_finalize = any(h.get("action") == "orchestrate_result" and (h.get("meta") or {}).get("action") == "finalize" for h in history)

        if not has_select:
            return "planned"
        if has_select and not has_chat:
            return "asked"
        if has_chat and not has_finalize:
            return "chatted"
        return "planned"
