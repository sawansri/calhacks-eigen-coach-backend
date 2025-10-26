#!/usr/bin/env python3

"""Quick helper to test the finalizer endpoint."""

import asyncio
from datetime import datetime
import httpx

PAYLOAD = {
    "student_data": {
        "student_name": "Alice",
        "exam_name": "SAT Math",
        "memory": [
            "Struggles with geometry",
            "Strong in algebra"
        ]
    },
    "conversation_history": "[tutor]: 'What is the sum of the angles in a triangle?' [student]: 'I think it might be 180 degrees. Because I am so good at geometry.' [tutor]: 'That is correct! The sum of all angles in any triangle is always 180 degrees.' [student]: 'Great! Can you explain why?' [tutor]: 'Sure! Imagine a triangle on a flat piece of paper. If you extend each side of the triangle into a line, the angles you have created on a straight line always sum to 180 degrees.' [student]: 'Oh, that makes sense now! Thank you!'"
}


async def main() -> None:
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            "http://localhost:8000/finalizer",
            json=PAYLOAD,
        )
        response.raise_for_status()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] response -> {response.json()}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
