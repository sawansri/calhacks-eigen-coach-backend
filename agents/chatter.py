# streaming AI chat agent, its only job is to chat back to the user. 
# It will receive the correct answer of the question and guide user through understanding the question
# It will never give the user the answer. Always guide the user through.
# It will tell user once they get it right.

from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ClaudeAgentOptions


class TutorChat:
    """Stateful chat client that guides a student through a tutoring session."""

    def __init__(self, student_data: dict, question_answer: str) -> None:
        """Set up the tutor agent for a new conversation session."""
        self.student_data = student_data
        self.question_answer = question_answer
        self.client = None
        self._is_connected = False

    def _build_system_prompt(self) -> str:
        """Construct the initial system prompt that encodes student context."""
        memory_items = self.student_data.get("memory", [])
        memory_context = "\n".join(f"- {item}" for item in memory_items) if memory_items else "- No prior context available"
        student_name = self.student_data.get("student_name", "Student")
        exam_name = self.student_data.get("exam_name", "Exam")

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
"""

    async def _connect(self):
        """Initializes and connects the ClaudeSDKClient."""
        if not self.client:
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
            self.client = ClaudeSDKClient(options=options)
            await self.client.connect() # Manually connect
            self._is_connected = True

    async def chat(self, user_message: str) -> str:
        """Send a message to Claude and get the complete response."""
        try:
            if not self._is_connected:
                await self._connect()

            await self.client.query(user_message)

            response_text = ""
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
            
            return response_text or "I'm here to help! What would you like to discuss?"

        except Exception as exc:
            print(f"Error in chat: {exc}")
            self._is_connected = False # Mark as disconnected on error
            return "I encountered an error. Please try again."

    async def close(self):
        """Disconnects the client if it is connected."""
        if self.client and self._is_connected:
            await self.client.disconnect()
            self._is_connected = False
            self.client = None