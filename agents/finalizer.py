# Performance evaluation agent for analyzing student conversations
# Outputs scores to update skill levels in the memory database

import json
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)
from database.db_helpers import get_skill_levels, set_skill_level


def get_unique_topics_helper():
    """Helper to get unique topics from question bank."""
    from database.db import DatabaseManager
    
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        query_sql = """
            SELECT DISTINCT topic_tag1 FROM questions 
            UNION 
            SELECT DISTINCT topic_tag2 FROM questions
            UNION
            SELECT DISTINCT topic_tag3 FROM questions
            WHERE topic_tag3 IS NOT NULL
        """
        cursor.execute(query_sql)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [(row[0], 0) for row in results if row[0]]
    except Exception:
        return []


def _parse_conversation_string(conversation_str: str) -> str:
    """Parse conversation from format: [tutor]: 'message' [student]: 'message'
    
    Args:
        conversation_str: String in format [tutor]: 'msg' [student]: 'msg' ...
        
    Returns:
        Formatted conversation text
    """
    if isinstance(conversation_str, str):
        # Replace [tutor]: with "Tutor: " and [student]: with "Student: "
        formatted = conversation_str.replace("[tutor]: '", "Tutor: ").replace("[student]: '", "\nStudent: ").replace("' ", " ")
        return formatted
    return ""


async def finalizer_agent(student_data: dict, conversation_history):
    """Analyze student performance and provide skill level scores.
    
    Args:
        student_data: Dictionary with student info (exam_name, student_name, memory)
        conversation_history: Either a string in format "[tutor]: 'msg' [student]: 'msg' ..." 
                            or a list of dicts with role/content keys
    
    Returns:
        Score deltas in format {topic: score} for each topic covered
    """
    student_name = student_data.get("student_name", "default")
    exam_name = student_data.get("exam_name", "default")
    
    # Get current skill levels and available topics
    skill_levels = get_skill_levels()
    current_skills = {t: l for t, l in skill_levels}
    topics = get_unique_topics_helper()
    topics_list = ", ".join([t[0] if isinstance(t, tuple) else t for t in topics if not isinstance(topics, str)]) if topics and not isinstance(topics, str) else "general"
    
    # Build context strings
    # Handle both string format and list format for conversation history
    if isinstance(conversation_history, str):
        conversation_text = _parse_conversation_string(conversation_history)
    elif isinstance(conversation_history, list):
        conversation_text = "\n".join([f"{m.get('role', 'unknown')}: {m.get('content', '')}" for m in conversation_history])
    else:
        conversation_text = str(conversation_history)
    
    skills_context = "\n".join([f"- {t}: {l}" for t, l in current_skills.items()]) or "- No prior skills"
    memory_context = "\n".join(f"- {item}" for item in student_data.get("memory", [])) or "- No prior context"
    
    prompt = f"""Analyze this tutoring session and score the student's performance:

Student: {student_name}
Exam: {exam_name}

Available Topics: {topics_list}
Current Skills: {skills_context}
Student Background: {memory_context}

Session Conversation:
{conversation_text}

Return ONLY valid JSON with topic names as keys and scores (0-100) as values. Example: {{"algebra": 45, "geometry": 75}}
ONLY return topics that are relevant to the conversation above!
"""

    options = ClaudeAgentOptions(
        model="haiku",
        system_prompt="""You are a performance evaluator. Analyze conversation and estimate student scores (0-100 scale: 0-25=novice, 26-50=beginner, 51-75=intermediate, 76-100=advanced). Return ONLY valid JSON with format: {"topic": score, ...}. No other text.""",
        permission_mode='acceptEdits',
        mcp_servers={
            "database": {"command": "-m", "args": ["database.db_mcp"]}
        }
    )

    result_text = ""
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)   

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            result_text += block.text
    except Exception as e:
        print(f"Error in finalizer query: {e}")

    cleaned_text = result_text.strip()
    print(f"Finalizer cleaned text: {cleaned_text}")
    
    # Strip markdown code blocks if present
    if cleaned_text.startswith("```"):
        # Remove opening ```json or ``` and closing ```
        cleaned_text = cleaned_text.split("```")[1]
        # Remove optional json/python/etc language identifier
        if cleaned_text.startswith("json") or cleaned_text.startswith("python"):
            cleaned_text = cleaned_text[4:].lstrip()
        cleaned_text = cleaned_text.strip()
    
    print(f"Finalizer cleaned text: {cleaned_text}")
    if not cleaned_text:
        return None

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"Finalizer returned invalid JSON: {e}")
        print(f"Attempted to parse: {cleaned_text}")
        return None

    if not isinstance(result, dict):
        print("Finalizer returned unexpected data type, falling back to default score")
        return None

    # print(f"Finalizer cleaned text: {cleaned_text}")
    # for topic, score in result.items():
    #     set_skill_level(topic, score)
    return result