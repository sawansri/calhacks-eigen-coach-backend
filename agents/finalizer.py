# This agent collects conversation history and gives a score reflecting a student's performance.
# one shot agent to analyze session and provide performance feedback
# it outputs scores, which we use to update skill levels in memory. Like say current skill evel is 10, with an estimation of 50,
# we update skill level to say 20, based on some criteria.

import asyncio
import sys
# sys.path.insert(0, '/Users/joe/repostories/calhacks/backend')

from claude_agent_sdk import query, ClaudeAgentOptions
from memory.memory_mcp import get_skill_level_pairs_helper
from question_bank.qb_mcp import get_unique_topics_helper

async def finalizer_agent(student_data: dict, conversation_history: list):
    """Analyze student performance and provide skill level score deltas.
    
    Args:
        student_data: Dictionary with student info (exam_name, student_name, memory)
        conversation_history: List of conversation exchanges
    
    Returns:
        Score deltas in format {topic: delta} for each topic covered
    """
    # Get current skill levels
    skill_levels = get_skill_level_pairs_helper()
    if isinstance(skill_levels, str):
        skill_levels = []
    
    # Convert to dict for easier lookup
    current_skills = {topic: level for topic, level in skill_levels}
    
    # Get unique topics
    topics = get_unique_topics_helper()
    if isinstance(topics, str):
        topics = []
    
    # Format topics list
    topics_list = ", ".join([t if isinstance(t, str) else t[0] for t in topics])
    
    options = ClaudeAgentOptions(
        system_prompt="""You are a performance evaluation agent for an intelligent tutoring system.

SKILL LEVEL SCORING SCALE (0-100):
- 0-25: Novice - Minimal understanding, needs significant guidance
- 26-50: Beginner - Basic understanding, makes mistakes frequently
- 51-75: Intermediate - Solid understanding, occasional mistakes
- 76-100: Advanced - Strong mastery, consistent accuracy

Your job is to:
1. Analyze the conversation history between tutor and student
2. Evaluate the student's understanding and performance on each topic covered
3. For each topic mentioned in the conversation:
   - Compare their demonstrated understanding to the scoring scale
   - Calculate the score delta (change from their current level)
   - Positive delta = improvement, negative delta = decline (if applicable)
   - Use increments of 5 (e.g., +10, -5, +15)
4. Return ONLY a JSON object with score deltas for topics where there was measurable change

Return your analysis in EXACTLY this format:
{
  "topic_name": current_score_estimation,
  "topic_name_2": current_score_estimation
}

Example: {"calculus": 12, "geometry": 99, "algebra": 0}

Do not include explanations or any other text - ONLY the JSON object.""",
        permission_mode='acceptEdits',
        # cwd="/Users/joe/repostories/calhacks/backend",
        mcp_servers={
            "memory": {
                "command": "python",
                "args": ["memory/memory_mcp.py"]
            },
            "question_bank": {
                "command": "python",
                "args": ["question_bank/qb_mcp.py"]
            }
        }
    )

    # Format conversation and student context for the prompt
    conversation_text = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in conversation_history])
    student_name = student_data.get("student_name", "Student")
    exam_name = student_data.get("exam_name", "Exam")
    memory_context = "\n".join(f"- {item}" for item in student_data.get("memory", []))
    
    # Build current skill levels context
    skills_context = "\n".join([f"- {topic}: {level}" for topic, level in current_skills.items()])

    prompt = f"""Analyze this tutoring session and provide score deltas:

Student: {student_name}
Exam: {exam_name}

Available Topics: {topics_list}

Current Skill Levels:
{skills_context if skills_context else "- No prior skills recorded"}

Student Background:
{memory_context if memory_context else "- No prior context available"}

Conversation History:
{conversation_text}

Evaluate the student's performance on each topic covered and provide score deltas."""

    async for message in query(
        prompt=prompt,
        options=options
    ):
        # Parse and return the JSON response
        import json
        try:
            result = json.loads(message.content)
            return result
        except json.JSONDecodeError:
            return message.content
