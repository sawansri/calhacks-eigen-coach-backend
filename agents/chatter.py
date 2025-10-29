# streaming AI chat agent, its only job is to chat back to the user. 
# It will receive the correct answer of the question and guide user through understanding the question
# It will never give the user the answer. Always guide the user through.
# It will tell user once they get it right.

import base64
import json
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ClaudeAgentOptions


class TutorChat:
    """Stateful chat client that guides a student through a tutoring session."""

    def __init__(self, student_data: dict, question_answer: str) -> None:
        """Set up the tutor agent for a new conversation session."""
        self.student_data = student_data
        self.question_answer = question_answer
        self.client = None
        self._is_connected = False
        self.correct_status = False  # Track if the student has answered correctly

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
5. Encourage progress and celebrate correct understanding. Help with adjacent concepts too.
6. When the student shares useful learning information (learning style, strengths, weaknesses, interests), call the add_memory_entry tool to save it.
7. Limit your responses to 150 words or less.
8. Always include the correct_status in your response.

YOU ALWAYS RESPOND in FORMAT:
{{""response": [advice and guidance, in string, not JSON], "correct_status": [true/false]}}
No matter what, do not write outside the json format.
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

    def _read_image_as_base64(self, image_path: str) -> str:
        """Read an image file and convert it to base64 string."""
        try:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            with open(path, "rb") as image_file:
                return base64.standard_b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error reading image: {e}")
            raise

    def _get_image_media_type(self, image_path: str) -> str:
        """Determine the media type based on file extension."""
        suffix = Path(image_path).suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(suffix, "image/jpeg")

    async def chat(self, user_message: str, contains_image: bool = False) -> str:
        """Send a message to Claude and get the complete response.
        
        Args:
            user_message: The text message from the user
            contains_image: Whether the message includes an image
            image_path: Path to the image file in /tmp (required if contains_image is True)
        """
        try:
            image_path = "/Users/joe/repostories/calhacks/backend/tmp/image.jpeg"
            if not self._is_connected:
                await self._connect()

            # Build the query with image support if applicable
            print(contains_image, image_path)
            if contains_image and image_path:
                # Read image and convert to base64
                image_base64 = self._read_image_as_base64(image_path)
                media_type = self._get_image_media_type(image_path)
                
                # Create a message with both text and image
                # Claude SDK will handle the image in the context of the query
                query_message = f"{user_message}\n\n[Image attached: {image_path}]"
                
                # Add the image as context for Claude to read
                await self.client.query(
                    query_message,
                    image_data={
                        "base64": image_base64,
                        "media_type": media_type,
                        "source": image_path
                    }
                )
            else:
                await self.client.query(user_message)

            response_text = ""
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
            
            # Parse the nested JSON response and extract the actual data
            try:
                # Remove "```json" and all newline characters
                response_text = response_text.replace("```json", "").replace("\n", "").replace("```", "")
                return response_text
            except json.JSONDecodeError:
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