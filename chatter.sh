
#!/bin/bash

# Example test query for the chatter endpoint
# This script tests the tutoring chat functionality

curl -X POST http://localhost:8000/chatter \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON'
{
  "user_message": "I think the answer involves adding the angles, but I'm not sure how to start.",
  "question_answer": "The sum of angles in a triangle is 180 degrees",
  "conversation_history": [
    {
      "tutor": "What is the sum of the angles in a triangle?",
      "student": "I know triangles have three sides and three angles."
    }
  ]
}
JSON


