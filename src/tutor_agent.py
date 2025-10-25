
import claude_agent_sdk

class TutorAgent(claude_agent_sdk.Tool):
    def __init__(self):
        super().__init__(
            name="tutor_agent",
            description="Retrieves exam questions and generates new questions.",
            inputs=[
                claude_agent_sdk.ToolParam(name="topic", type="str", description="The topic to get a question for."),
            ],
            output_type="str"
        )

    def __call__(self, topic: str) -> str:
        # In a real implementation, this would involve retrieving questions
        # from a database or generating new ones.
        print(f"Getting question for topic: {topic}")
        return f"Here is a question about {topic}"

