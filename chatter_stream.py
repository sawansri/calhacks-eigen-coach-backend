#!/usr/bin/env python3

"""Quick helper to view streaming responses from the chatter endpoint."""

import asyncio
from datetime import datetime
import httpx

PAYLOAD = {
    "user_message": "Can you help me reason through the triangle angle sum?",
    "question_answer": "The sum of angles in a triangle is 180 degrees",
    "conversation_history": [
        {
            "tutor": "What is the sum of the angles in a triangle?",
            "student": "I think it might be 180 but I am not positive."
        }
    ]
}


async def main() -> None:
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/chatter/stream",
            json=PAYLOAD,
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                if chunk:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] chunk -> {chunk!r}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
