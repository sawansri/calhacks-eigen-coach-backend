import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def question_agent(current_date):
    options = ClaudeAgentOptions(
        system_prompt="""You are a question selection agent for an intelligent tutoring system.
Your job is to:
1. Check the calendar and use get_topics_by_date to get list of topics and number of questions for the current date
2. Query the question bank MCP server to get available questions by topic
3. Select questions based on the selected topics and number of questions
4. If many questions have been asked before, prioritize those that have not been asked yet.
5. You can also generate appropriate questions if all questions have been asked before. 
Make sure to use the same format as existing questions. Just swap values.
6. Return the selected question in a list of format "Selected Question: {question_prompt} | 
Answer: {answer} | Explanation: {explanation} | Difficulty: {difficulty} | Topic Tags: {topic_tags}"

Use the available MCP tools to access question bank data and user memory.""",
        permission_mode='acceptEdits',
        cwd="/Users/joe/repostories/calhacks/backend",
        mcp_servers={
            "question_bank": {
                "command": "python",
                "args": ["question_bank/qb_mcp.py"]
            },
            "memory": {
                "command": "python",
                "args": ["memory/memory_mcp.py"]
            }
        }
    )

    async for message in query(
        prompt="Select an appropriate question from the question bank for the current user session. The current date is " + current_date,
        options=options
    ):
        return message.content
