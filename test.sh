curl -X GET http://localhost:8000/health

curl -X POST http://localhost:8000/initializer \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "student_name": "Maria Silva",
      "exam_name": "ENEM 2025",
      "memory": []
    },
    "date": "2025-01-15"
  }'

curl -X POST http://localhost:8000/questioner \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "student_name": "Maria Silva",
      "exam_name": "ENEM 2025",
      "memory": []
    },
    "date": "2025-01-15"
  }'

curl -X POST http://localhost:8000/chatter \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "student_name": "Maria Silva",
      "exam_name": "ENEM 2025",
      "memory": ["Student prefers visual explanations"]
    },
    "user_message": "I think the answer involves calculus, but I am not sure how to start",
    "conversation_history": []
  }'

curl -X POST http://localhost:8000/finalizer \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "student_name": "Maria Silva",
      "exam_name": "ENEM 2025",
      "memory": []
    },
    "conversation_history": [
      {
        "role": "user",
        "content": "I think the answer is 42"
      },
      {
        "role": "assistant",
        "content": "Good start! Can you explain how you arrived at that number?"
      },
      {
        "role": "user",
        "content": "I used the quadratic formula and got x = 42"
      },
      {
        "role": "assistant",
        "content": "Excellent! You correctly applied the quadratic formula."
      }
    ]
  }'
