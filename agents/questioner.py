"""Questioner agent for selecting appropriate questions for students."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)

from database.db_helpers import get_calendar_entry, get_questions_by_topic, get_skill_levels


async def question_agent(current_date: str) -> List[Dict[str, Any]]:
    """Select questions tailored to the student's scheduled topics and skill levels."""
    print(f"Starting question selection for date: {current_date}")

    calendar_entry = get_calendar_entry(current_date)
    print(f"Calendar entry for {current_date}: {calendar_entry}")
    topics: List[str] = calendar_entry.get("topics", []) if calendar_entry else []
    if not topics:
        print(f"No topics found for date {current_date}")
        return []

    print(f"Found topics: {topics}")
    skill_pairs = get_skill_levels()
    skill_levels = {topic: level for topic, level in skill_pairs}
    print(f"Student skill levels: {skill_levels}")

    questions_by_topic: Dict[str, List[Dict[str, Any]]] = {}
    for topic in topics:
        topic_questions = get_questions_by_topic(topic)
        print(f"Found {len(topic_questions)} questions for topic: {topic}")
        if topic_questions:
            questions_by_topic[topic] = [
                {
                    "question_prompt": question.get("question_prompt"),
                    "topic_tag1": question.get("topic_tag1"),
                    "topic_tag2": question.get("topic_tag2"),
                    "topic_tag3": question.get("topic_tag3"),
                    "answer": question.get("answer"),
                    "explanation": question.get("explanation"),
                    "difficulty": question.get("difficulty"),
                    "has_been_asked": question.get("has_been_asked"),
                    "source_topic": topic,
                }
                for question in topic_questions
            ]

    if not questions_by_topic:
        print("No questions available for any topic")
        return []

    print(f"Querying Claude agent for question selection")
    payload = {
        "scheduled_topics": topics,
        "skill_levels": skill_levels,
        "questions_by_topic": questions_by_topic,
    }

    options = ClaudeAgentOptions(
        model="haiku",
        system_prompt=(
            "You are a question selection engine for an intelligent tutoring system. "
            "Always respond with valid JSON only."
        ),
        permission_mode="acceptEdits",
    )

    prompt = (
        "Given the scheduled topics, student skill levels, and candidate questions, "
        "select at most one question per topic. Choose questions that best match the student's "
        "skill level (lower skill levels should receive easier questions)."
        "you should deprioritize questions that have been asked before, and prefer those that have not been asked yet."
        "If a question does not have a solution or answer, come up with your own solution or answer, and fill your response."
        "you can create new questions if most existing ones have been asked before. Example is replacing values while keeping format the same."
        "\n\nRules:\n"
        "- Return a JSON array.\n"
        "- Each element must include the keys: question_prompt, topic_tag1, topic_tag2, topic_tag3, answer, explanation, difficulty, has_been_asked, source_topic, selection_reason.\n"
        "- Only include topics present in scheduled_topics.\n"
        "- Do not include any additional text outside the JSON array.\n\n"
        f"Data payload:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    response_text = ""
    try:
        print("Making request to Claude agent")
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text

    except Exception as exc:
        print(f"Error in question_agent: {exc}")
        return []

    response_text = response_text.strip()
    if not response_text:
        print("Claude agent returned empty response")
        return []

    try:
        print("Parsing Claude agent response")
        selected_questions = json.loads(response_text)
        if isinstance(selected_questions, list):
            print(f"Successfully selected {len(selected_questions)} questions")
            return selected_questions
    except json.JSONDecodeError:
        print("Question agent returned invalid JSON payload; falling back to deterministic selection")

    fallback: List[Dict[str, Any]] = []
    for topic in topics:
        candidates = questions_by_topic.get(topic)
        if candidates:
            fallback_question = dict(candidates[0])
            fallback_question.setdefault("source_topic", topic)
            fallback_question["selection_reason"] = "Default selection due to invalid model response"
            fallback.append(fallback_question)
            print(f"Using fallback question for topic: {topic}")

    print(f"Returning {len(fallback)} fallback questions")
    return fallback
