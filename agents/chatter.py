# streaming AI chat agent, its only job is to chat back to the user. 
# It will receive the correct answer of the question and guide user through understanding the question
# It will never give the user the answer. Always guide the user through.
# It will tell user once they get it right.

from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ClaudeAgentOptions


class TutorChat:
    """Streaming chat client that guides a student through a tutoring session."""

    def __init__(self, student_data: dict, question_answer: str, conversation_history: list) -> None:
        """Set up tutor context for the current chat session."""
        self.student_data = student_data
        self.question_answer = question_answer
        self.conversation_history = conversation_history

    def _build_system_prompt(self) -> str:
        """Construct a system prompt that encodes student context and history."""
        memory_items = self.student_data.get("memory", [])
        memory_context = "\n".join(f"- {item}" for item in memory_items) if memory_items else "- No prior context available"
        student_name = self.student_data.get("student_name", "Student")
        exam_name = self.student_data.get("exam_name", "Exam")

        conversation_transcript = "".join(
            f"Tutor: {entry.get('tutor', '')}\nStudent: {entry.get('student', '')}\n"
            for entry in self.conversation_history
        )

        return f"""You are a helpful tutor guiding {student_name} through {exam_name}.

Student Context:
- Name: {student_name}
- Exam: {exam_name}
- Question Answer: {self.question_answer}
- Prior knowledge:
{memory_context}

Guidelines:
1. Guide the student through understanding WITHOUT giving away the answer
2. Ask clarifying questions to help them think deeper
3. If they provide an answer, validate it appropriately
4. Never directly give the answer - help them discover it
5. Encourage progress and celebrate correct understanding
6. When the student shares useful learning information (learning style, strengths, weaknesses, interests), call the add_memory_entry tool to save it.

Conversation so far:
{conversation_transcript}
"""

    async def chat(self, user_message: str) -> str:
        """Stream a response from Claude for the supplied user message."""
        options = ClaudeAgentOptions(
            model="haiku",
            system_prompt=self._build_system_prompt(),
            permission_mode="acceptEdits",
            mcp_servers={
                "database": {
                    "command": "-m",
                    "args": ["database.db_mcp"],
                }
            },
        )

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(user_message)

                response_text = ""
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_text += block.text

                if response_text:
                    return response_text

                return "I'm here to help! What would you like to discuss?"

        except Exception as exc:
            print(f"Error in chat: {exc}")
            return "I encountered an error. Please try again."