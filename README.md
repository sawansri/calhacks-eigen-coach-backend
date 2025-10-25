# calhacks-eigen-coach-backend

AI powered tutor for exam prep, backstory is that in Brazilian public schools, students don't have the resources to hire private tutors and the exams are too obscure to be featured on websites like KhanAcademy. Our app essentially provides this platform, all users have to do is upload papers and our agents will create a time-aware study guide, with a question bank, flexible question generating, and memory to store progress by topic

## Time-awareness --> study timeline
Question Bank Agent determines tags/question topics, use math/algorithms + sensible study defaults (hours per day, etc) to come up with a plan, no llm needed here

## Question Bank --> tags and topics
Question Bank Agent processes exam, determines exam, determines topics per exam

### Question Bank (MySQL) and Memory (TinyDB via MCP)

#### Pre-processing before inserting into DB
Need LLM or simple rules to process exams, extracting exam type, and labeling each question by topic (tagging them). Tagged questions are stored in MySQL.

## Flexible --> no pre-designing, generate on the go

## Memory --> progress tracking by topic




## Agentic Architecture powered by Claude Agent SDK in Python (https://docs.claude.com/en/api/agent-sdk/python)

Data Sources

User uploads

Official resources

Other info?

Topic explanations?

Extracted questions (tagged)

Proctoring guidelines, etc.

Features

Study timeline

Tags and topics (question bank)

No pre-designing

Track progress

User State (JSON or TinyDB)

Single JSON file (e.g., user_state.json) or TinyDB collections to store persistent user data.

User preferences (e.g., subjects, difficulty).

User progress (e.g., questions answered, scores by topic).

Feedback history.

Agent Architecture

Student (User)

Provides user queries

Provides docs

Provides preferences

Orchestrator Agent

Sends requests to the appropriate agent

Receives agent responses

Reads from and writes to user_state.json to update state.

1. Document Ingestion (Exam Processor) Agent

Parses uploads

Structures and tags data

Outputs: Docs and labeled data (to be stored in MySQL question bank).

2. Planner (Scheduler) Agent

Inputs: Takes exam data (from RAG) and user preferences (from user_state.json).

Action: Creates a custom plan and data schedule.

Outputs: Updates the plan in user_state.json.

3. Tutor Agent

Action: Retrieves exam questions (based on topic, difficulty, etc.) from the RAG layer.

Note: May call another agent for new question generation.

4. Feedback (Grader) Agent

Action: Generates feedback on a user's answer.

Outputs: Updates progress and feedback history by writing to user_state.json.

5. Scraper Agent (Optional)

Searches for external test banks, resources, etc.

Data Storage

MySQL (Question Bank)

Stores tagged questions with prompts, answers, explanations, difficulty, topic tags, and asked flags. Managed via `question_bank/qb.py` and exposed to agents via the Question Bank MCP (`question_bank/qb_mcp.py`).

TinyDB (Memory/Calendar/Skills via Memory MCP)

Lightweight non-SQL storage for:
- Memory (long-term student notes)
- Calendar (date → topics, n_questions)
- Skill levels (per-topic scores)

Exposed to agents via the Memory MCP (`memory/memory_mcp.py`).

JSON File (user_state.json)

Optional storage for user preferences, progress, and feedback history. Currently not wired into agents.

## Current Implementation Status

- Implemented:
  - Question Bank initialization in MySQL (`question_bank/qb.py`).
  - Question Bank MCP (`question_bank/qb_mcp.py`):
    - `get_question_by_topic`, `get_unique_topics` (+ helper).
  - Memory MCP (`memory/memory_mcp.py`):
    - `get_topics_by_date`, `get_skill_level_pairs`, `add_memory_entry`, `write_to_database`.
  - Agents:
    - Question selection agent (`agents/questioner.py`) uses both MCPs.
    - Tutor chat agent (`agents/chatter.py`) with streaming chat and Memory MCP.
    - Session finalizer (`agents/finalizer.py`) computes topic score deltas using MCPs.
  - Minimal FastAPI app (`api.py`) with placeholder endpoints for storing values; to be expanded to orchestrate agents.

- Planned/To-do:
  - Document ingestion pipeline to parse uploads and insert tagged questions into MySQL.
  - Rule-based Planner to populate TinyDB calendar with topics by date and number of questions.
  - Expand FastAPI to expose endpoints for calendar seeding, question selection, chat, and session finalization.
  - Seeding scripts for MySQL (sample questions) and TinyDB (calendar/memory/skill levels).
  - Optional: RAG/vector store integration if needed (not currently used).

## Local Development

1) Dependencies

```
pip install -r requirements.txt
```

2) MySQL for Question Bank

- The code expects MySQL at `localhost:8003` with user `root` and a password configured in `question_bank/qb.py`.
- Initialize database and table:

```
python -m question_bank.qb
```

3) Memory MCP and TinyDB

- MCP processes are launched by agents automatically. TinyDB JSON files are created in `db/` on first write.

4) Run API (work in progress)

```
uvicorn api:app --reload
```

## Notes

- ChromaDB is no longer used. The system now relies on MySQL for the question bank and TinyDB (via MCP) for memory/calendar/skills.
