#!/usr/bin/env python3

"""Quick helper to send a single request to the chatter endpoint."""

import asyncio
from datetime import datetime
import httpx

PAYLOAD = {
    "session_id": "demo-session",
    "user_message": "[tutor]: 'what is the sum of the angles in a triangle?' [student]: 'The sum of angles in a triangle is 270 degrees'",
    "question_answer": "180 degrees",
}

PAYLOAD_2 = {
    "session_id": "demo-session2",
    "user_message": "[student]: 'Okay can you explain a bit more about it?'",
    "question_answer": "180 degrees",
}


async def main() -> None:
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            "http://localhost:8000/chatter",
            json=PAYLOAD,
        )
        response.raise_for_status()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] response -> {response.json()}", flush=True)
    
        response2 = await client.post(
            "http://localhost:8000/chatter",
            json=PAYLOAD_2,
        )
        response2.raise_for_status()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] response2 -> {response2.json()}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
