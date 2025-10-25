import json
from typing import Any, Dict, List
from datetime import datetime
import logging
import os

from claude_agent_sdk import query, ClaudeAgentOptions
from memory.memory import get_db


SYSTEM_PROMPT = """
You are the Orchestration Agent for a tutoring system. Your job is to decide the next step
in a user's study session based on the current date, calendar, recent session history, and the user's request.

Available MCP tools (invoked by the host as needed):
- memory.get_topics_by_date(date): read topics and n_questions for a date
- memory.write_to_database(db_name, data): write JSON to TinyDB (use db_name='calendar' to update the plan)
- question_bank.get_unique_topics(): list topics from the question bank
- question_bank.get_question_by_topic(topic): peek questions in a topic

Rules:
1) If the user requests a schedule change (e.g., add/remove topics or adjust quantities), propose a calendar update
   (db_name='calendar', data={"date": "YYYY-MM-DD", "topics": [...], "n_questions": N}).
2) If there is no calendar entry for today, propose seeding a minimal plan.
3) If plan exists and no question has been selected yet, propose selecting a question.
4) If a question has been asked and the user is responding, propose chat.
5) If a chat has completed, propose finalization.

Return ONLY a compact JSON object with this structure:
{
  "action": "seed_calendar" | "select_question" | "chat" | "finalize",
  "args": { ... },
  "side_effects": [
     {"type": "calendar_write", "db_name": "calendar", "data": {"date": "YYYY-MM-DD", "topics": [...], "n_questions": N}}
  ]
}
No extra commentary.
"""


def _get_recent_history(session_id: str, date: str, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        db = get_db("orchestrator")
        items = [r for r in db.all() if r.get("session_id") == session_id and r.get("date") == date]
        items.sort(key=lambda r: r.get("ts", 0), reverse=True)
        return items[:limit]
    except Exception:
        return []


def _infer_session_id(student_data: Dict[str, Any], date: str) -> str:
    name = (student_data.get("student_name") or "anon").strip() or "anon"
    return f"{name}:{date}"


async def orchestrate_llm(payload: Dict[str, Any]) -> Dict[str, Any]:
    log = logging.getLogger("orchestrator_llm")
    date = payload.get("date") or datetime.now().strftime('%Y-%m-%d')
    student_data = payload.get("student_data") or {}
    session_id = payload.get("session_id") or _infer_session_id(student_data, date)
    user_input = payload.get("user_input") or ""
    # Log derived session details
    try:
        log.debug(f"orchestrate_llm: session_id={session_id}, date={date}, user_input_len={len(user_input) if isinstance(user_input, str) else 'n/a'}")
    except Exception:
        pass

    # Prepare context for the LLM
    history = _get_recent_history(session_id, date)
    try:
        log.debug(f"orchestrate_llm: recent_history_count={len(history)}")
    except Exception:
        pass
    context = {
        "date": date,
        "student_data": student_data,
        "recent_history": history,
        "user_input": user_input,
    }

    # Ensure MCP servers launch from project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    options = ClaudeAgentOptions(
        model="claude-4.5-haiku-latest",
        system_prompt=SYSTEM_PROMPT,
        permission_mode='acceptEdits',
        cwd=project_root,
        mcp_servers={
            "memory": {"command": "python", "args": ["memory/memory_mcp.py"]},
            "question_bank": {"command": "python", "args": ["question_bank/qb_mcp.py"]},
        },
    )

    # Ask the LLM to produce the plan JSON
    prompt = (
        "Decide the next step given this context. Return ONLY the JSON as specified.\n\n" +
        json.dumps(context)
    )

    last_assistant_text = None
    try:
        log.debug("orchestrate_llm: starting query stream to LLM")
        async for msg in query(prompt=prompt, options=options):
            role = getattr(msg, "role", None)
            content = getattr(msg, "content", None)
            # Only consider assistant messages for plan JSON
            try:
                log.debug(f"orchestrate_llm: stream msg role={role}, has_content={bool(content)}")
            except Exception:
                pass
            if role == "assistant" and content:
                last_assistant_text = content
                try:
                    plan = json.loads(content)
                    log.info("orchestrate_llm: parsed assistant JSON plan")
                    return plan
                except Exception:
                    # keep iterating to see if a later assistant msg has clean JSON
                    pass
    except Exception as e:
        # Surface internal errors to server logs; API layer will return generic 500
        log.error(e, stack_info=True)
        log.error(f"LLM orchestrator failed: {e}", stack_info=True)

    # Fallbacks
    if last_assistant_text:
        try:
            plan = json.loads(last_assistant_text)
            log.info("orchestrate_llm: returning plan from last assistant message (fallback)")
            return plan
        except Exception:
            log.warning("orchestrate_llm: last assistant message not valid JSON; returning raw text")
            return {"raw": last_assistant_text}
    log.warning("orchestrate_llm: no assistant content received; returning sentinel")
    return {"raw": "no_assistant_content"}
