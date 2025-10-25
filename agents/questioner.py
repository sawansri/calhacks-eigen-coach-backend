"""Questioner agent for selecting appropriate questions for students."""

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)


async def question_agent(current_date: str) -> str:
    """
    Select an appropriate question from the question bank.
    
    Args:
        current_date: Date for selecting questions in YYYY-MM-DD format
        
    Returns:
        Selected question text
    """
    options = ClaudeAgentOptions(
        system_prompt="""You are a question selection agent for an intelligent tutoring system.

Your job is to:
1. Use get_topics_by_date to check what topics are scheduled for today
2. Use get_question_by_topic to retrieve questions for those topics
3. Select the best question based on student skill levels
4. Return ONLY the question text, nothing else

Available MCP tools:
- get_topics_by_date(student_name, exam_name, date): Get scheduled topics
- get_question_by_topic(topic): Get questions for a topic
- get_skill_level_pairs(student_name, exam_name): Get current skill levels""",
        permission_mode='acceptEdits',
        mcp_servers={
            "database": {
                "command": "-m",
                "args": ["database.db_mcp"]
            }
        }
    )

    response_text = ""
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                prompt=(
                    "Select an appropriate question for the current user session. "
                    f"The current date is {current_date}."
                )
            )

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text

    except Exception as e:
        print(f"Error in question_agent: {e}")
        response_text = "Error selecting question. Please try again."
    
    return response_text.strip() if response_text else "No question available."
