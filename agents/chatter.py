# streaming AI chat agent, its only job is to chat back to the user. 
# It will receive the correct answer of the question and guide user through understanding the question
# It will never give the user the answer. Always guide the user through.
# It will tell user once they get it right.

from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ClaudeAgentOptions


class TutorChat:
    """Chat client for tutoring that maintains student context and conversation history."""
    
    def __init__(self, student_data: dict):
        """Initialize the tutor chat with student data.
        
        Args:
            student_data: Dictionary with structure:
                {
                    "exam_name": str,
                    "student_name": str,
                    "memory": List[str]
                }
        """
        self.student_data = student_data
        self.client = None
        self._connected = False
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with student context."""
        memory_context = "\n".join(f"- {item}" for item in self.student_data.get("memory", []))
        student_name = self.student_data.get("student_name", "Student")
        exam_name = self.student_data.get("exam_name", "Exam")
        
        return f"""You are a helpful tutor guiding {student_name} through {exam_name}.

Student Context:
- Name: {student_name}
- Exam: {exam_name}
- Prior knowledge:
{memory_context if memory_context else "- No prior context available"}

Guidelines:
1. Guide the student through understanding WITHOUT giving away the answer
2. Ask clarifying questions to help them think deeper
3. If they provide an answer, validate it appropriately
4. Never directly give the answer - help them discover it
5. Encourage progress and celebrate correct understanding
6. When the student shares useful learning information (learning style, strengths, weaknesses, interests), call the add_memory_entry tool to save it."""
    
    async def chat(self, user_message: str) -> str:
        """Send a message and get a response from Claude.
        
        Args:
            user_message: The user's message
        
        Returns:
            Claude's response text
        """
        if self.client is None:
            # Create client with memory MCP server access
            options = ClaudeAgentOptions(
                model="claude-3-5-sonnet-20241022",
                system_prompt=self.system_prompt,
                permission_mode='acceptEdits',
                mcp_servers={
                    "database": {
                        "command": "-m",
                        "args": ["database.db_mcp"]
                    }
                }
            )
            self.client = ClaudeSDKClient(options=options)
        
        if not self._connected:
            await self.client.connect()
            self._connected = True
        
        try:
            # Query Claude with the message
            await self.client.query(user_message)
            
            response_text = ""
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
            
            return response_text if response_text else "I'm here to help! What would you like to discuss?"
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return "I encountered an error. Please try again."
    
    async def close(self) -> None:
        """Close the client connection."""
        if self.client:
            try:
                await self.client.disconnect()
                self._connected = False
            except Exception as e:
                print(f"Error closing client: {e}")