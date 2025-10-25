import json
from typing import Any, Dict, List
from datetime import datetime
import logging
import os
import sys
import traceback

from claude_agent_sdk import query, ClaudeAgentOptions
from memory.memory import get_db

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)


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
    log.info("=" * 80)
    log.info("orchestrate_llm: Starting orchestration")
    
    try:
        date = payload.get("date") or datetime.now().strftime('%Y-%m-%d')
        student_data = payload.get("student_data") or {}
        session_id = payload.get("session_id") or _infer_session_id(student_data, date)
        user_input = payload.get("user_input") or ""
        
        log.info(f"orchestrate_llm: session_id={session_id}")
        log.info(f"orchestrate_llm: date={date}")
        log.info(f"orchestrate_llm: student_name={student_data.get('student_name', 'unknown')}")
        log.info(f"orchestrate_llm: user_input_length={len(user_input) if isinstance(user_input, str) else 'n/a'}")
        
    except Exception as e:
        log.error(f"orchestrate_llm: Failed to parse payload: {e}")
        log.error(f"Traceback: {traceback.format_exc()}")
        return {"error": "Failed to parse payload", "details": str(e)}

    try:
        # Prepare context for the LLM
        history = _get_recent_history(session_id, date)
        log.info(f"orchestrate_llm: Retrieved {len(history)} recent history records")
    except Exception as e:
        log.error(f"orchestrate_llm: Failed to get history: {e}")
        log.error(f"Traceback: {traceback.format_exc()}")
        history = []
    
    context = {
        "date": date,
        "student_data": student_data,
        "recent_history": history,
        "user_input": user_input,
    }

    try:
        # Ensure MCP servers launch from project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        log.info(f"orchestrate_llm: project_root={project_root}")
        
        # Verify MCP server files exist
        memory_mcp_path = os.path.join(project_root, "memory", "memory_mcp.py")
        qb_mcp_path = os.path.join(project_root, "question_bank", "qb_mcp.py")
        
        if not os.path.exists(memory_mcp_path):
            log.error(f"orchestrate_llm: memory_mcp.py not found at {memory_mcp_path}")
        else:
            log.info(f"orchestrate_llm: memory_mcp.py found at {memory_mcp_path}")
            
        if not os.path.exists(qb_mcp_path):
            log.error(f"orchestrate_llm: qb_mcp.py not found at {qb_mcp_path}")
        else:
            log.info(f"orchestrate_llm: qb_mcp.py found at {qb_mcp_path}")
        
        options = ClaudeAgentOptions(
            model="haiku",
            system_prompt=SYSTEM_PROMPT,
            permission_mode='acceptEdits',
            cwd=project_root,
            mcp_servers={
                "memory": {
                    "command": "python3",
                    "args": ["-m", "memory.memory_mcp"],
                    "env": {"PYTHONPATH": project_root}
                },
                "question_bank": {
                    "command": "python3",
                    "args": ["-m", "question_bank.qb_mcp"],
                    "env": {"PYTHONPATH": project_root}
                },
            },
        )
        log.info("orchestrate_llm: ClaudeAgentOptions created successfully")
        
    except Exception as e:
        log.error(f"orchestrate_llm: Failed to create ClaudeAgentOptions: {e}")
        log.error(f"Traceback: {traceback.format_exc()}")
        return {"error": "Failed to configure agent options", "details": str(e)}

    # Ask the LLM to produce the plan JSON
    prompt = (
        "Decide the next step given this context. Return ONLY the JSON as specified.\n\n" +
        json.dumps(context)
    )
    log.info(f"orchestrate_llm: Prompt prepared (length={len(prompt)})")
    log.info(f"Prompt is: {prompt}")
    log.info(f"Context is: {json.dumps(context, indent=2)}")

    last_assistant_text = None
    message_count = 0
    
    try:
        log.info("orchestrate_llm: Starting query stream to LLM")
        async for msg in query(prompt=prompt, options=options):
            message_count += 1
            log.debug(f"orchestrate_llm: Received message #{message_count}")
            
            try:
                role = getattr(msg, "role", None)
                content = getattr(msg, "content", None)
                log.debug(f"orchestrate_llm: Message role={role}, content_length={len(content) if content else 0}")
                
                if role == "assistant" and content:
                    last_assistant_text = content
                    log.debug(f"orchestrate_llm: Assistant content: {content[:200]}...")
                    
                    try:
                        plan = json.loads(content)
                        log.info("orchestrate_llm: Successfully parsed assistant JSON plan")
                        log.info(f"orchestrate_llm: Plan action: {plan.get('action', 'unknown')}")
                        log.info("=" * 80)
                        return plan
                        
                    except json.JSONDecodeError as json_err:
                        log.warning(f"orchestrate_llm: JSON parse failed on message #{message_count}: {json_err}")
                        log.debug(f"orchestrate_llm: Failed content: {content}")
                        # Continue to next message
                        
            except Exception as msg_err:
                log.error(f"orchestrate_llm: Error processing message #{message_count}: {msg_err}")
                log.error(f"Traceback: {traceback.format_exc()}")
                continue
                
    except Exception as query_err:
        log.error(f"orchestrate_llm: Query stream failed: {query_err}")
        log.error(f"Traceback: {traceback.format_exc()}")
        log.error(f"orchestrate_llm: This usually means the MCP server failed to start")
        log.error(f"orchestrate_llm: Check MCP server stderr output above for details")
        
        # Try to return last assistant text as fallback
        if last_assistant_text:
            try:
                plan = json.loads(last_assistant_text)
                log.info("orchestrate_llm: Returning fallback plan from last assistant message")
                return plan
            except Exception as fallback_err:
                log.warning(f"orchestrate_llm: Fallback JSON parse failed: {fallback_err}")
                return {"error": "Query failed and fallback parsing failed", "raw": last_assistant_text}
        else:
            return {"error": "Query failed and no assistant content received"}

    # Final fallbacks
    if last_assistant_text:
        log.info(f"orchestrate_llm: Query completed with {message_count} messages; attempting final JSON parse")
        try:
            plan = json.loads(last_assistant_text)
            log.info("orchestrate_llm: Successfully parsed final assistant message")
            log.info(f"orchestrate_llm: Plan action: {plan.get('action', 'unknown')}")
            log.info("=" * 80)
            return plan
        except Exception as final_err:
            log.warning(f"orchestrate_llm: Final JSON parse failed: {final_err}")
            log.warning(f"orchestrate_llm: Returning raw text response")
            return {"raw": last_assistant_text}
            
    log.warning(f"orchestrate_llm: No assistant content received after {message_count} messages")
    log.warning("orchestrate_llm: Returning sentinel response")
    log.info("=" * 80)
    return {"raw": "no_assistant_content"}
