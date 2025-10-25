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




## Agentic Architecture

- **Orchestrator** (`agents/orchestrator.py`)
  - Central entry that routes tasks based on session stage: init → planned → asked → chatted.
  - Delegates to underlying agents and persists updates where needed.

- **Agents**
  - **Questioner** (`agents/questioner.py`): selects questions by date/topics using MCP tools.
  - **Tutor Chat** (`agents/chatter.py`): streaming Socratic tutoring; can save long-term notes via Memory MCP.
  - **Finalizer** (`agents/finalizer.py`): evaluates the session and returns topic score deltas; persists to TinyDB.

- **MCP Tools**
  - **Question Bank MCP** (`question_bank/qb_mcp.py`): fetch questions by topic, list topics.
  - **Memory MCP** (`memory/memory_mcp.py`): calendar (date → topics, n_questions), skill levels, memory, generic writes.

- **Storage**
  - **MySQL**: primary question bank (`question_bank/qb.py`).
  - **TinyDB**: calendar, skill levels, and long-term memory (`memory/memory.py`).

## Local Development

1) Install

```bash
pip install -r requirements.txt
```

2) MySQL (expects localhost:8003, user `root`, password in `question_bank/qb.py`)

```bash
# Run MySQL (example via Docker)
docker run -d --name calhacks-mysql -e MYSQL_ROOT_PASSWORD=joe_is_very_cool -p 8003:3306 mysql:8

# Initialize DB and table
python -m question_bank.qb
```

3) Run API (uvicorn)

```bash
python -m uvicorn main:app --reload
```

## Notes

- ChromaDB is not used. We use MySQL for the question bank and TinyDB (via MCP) for memory/calendar/skills.
