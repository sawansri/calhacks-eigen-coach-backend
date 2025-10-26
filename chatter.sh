
#!/bin/bash

# Simple interactive chat client for the /chatter endpoint

API_URL="http://localhost:8000/chatter"

# --- Static Data ---
# This would normally come from the questioner agent
QUESTION_ANSWER="The sum of angles in a triangle is 180 degrees."

# --- State ---
# Initialize conversation history as a JSON array
# Note: The 'tutor'/'student' roles in the history are illustrative; the current
# implementation uses a different format, but this demonstrates the concept.
CONVERSATION_HISTORY="[]"


echo "Starting interactive chat with TutorChat."
echo "Type 'exit' to end the session."
echo "-----------------------------------------"

while true; do
  # 1. Get user input
  read -p "You: " USER_MESSAGE

  # Exit condition
  if [[ "$USER_MESSAGE" == "exit" ]]; then
    echo "Ending chat session."
    break
  fi

  # 2. Construct the JSON payload
  # We use jq to safely embed the user message and history
  JSON_PAYLOAD=$(jq -n \
    --arg user_message "$USER_MESSAGE" \
    --arg question_answer "$QUESTION_ANSWER" \
    --argjson history "$CONVERSATION_HISTORY" \
    '{
      user_message: $user_message,
      question_answer: $question_answer,
      conversation_history: $history
    }')

  # 3. Send request to the API and get the response
  # The -s flag for curl makes it silent (no progress meter)
  API_RESPONSE=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD")

  # 4. Extract the assistant's response text
  # We use jq to parse the JSON response from the API
  ASSISTANT_RESPONSE=$(echo "$API_RESPONSE" | jq -r '.response')

  # Check for errors from the API
  if [[ -z "$ASSISTANT_RESPONSE" || "$ASSISTANT_RESPONSE" == "null" ]]; then
    echo "Error: Could not get a valid response from the server."
    echo "Server response: $API_RESPONSE"
    continue
  fi

  # 5. Print the assistant's response
  echo "Tutor: $ASSISTANT_RESPONSE"

  # 6. Update the conversation history
  # This is a simplified update; the actual format in _build_system_prompt is different
  CONVERSATION_HISTORY=$(echo "$CONVERSATION_HISTORY" | jq -c --arg user_msg "$USER_MESSAGE" --arg assistant_msg "$ASSISTANT_RESPONSE" '. + [{student: $user_msg, tutor: $assistant_msg}]')

done



