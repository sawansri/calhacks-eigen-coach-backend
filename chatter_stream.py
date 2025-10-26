#!/usr/bin/env python3

"""Quick helper to send a single request to the chatter endpoint."""

import asyncio
from datetime import datetime
import httpx

PAYLOAD = {
    "session_id": "demo-session",
    "user_message": "[tutor]: 'what is the sum of the angles in a triangle?' [student]: '200?'",
    "question_answer": "180 degrees",
}

PAYLOAD_2 = {
   "session_id": "demo-session",
   "user_message": "[student]: 'Okay, before that, can you tell me what is the formula in the image?'",
   "contains_image": "true"
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
