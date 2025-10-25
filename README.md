# Eigen Coach Backend

AI-powered tutor for exam prep. Built for Brazilian public schools where students lack resources for private tutors and standardized test preparation materials.

## 🎯 Core Features

- **Time-Aware Study Planning**: Generates personalized study schedules based on exam dates and student availability
- **Question Bank**: MySQL-backed question database with topic tagging and difficulty scoring
- **Student Memory**: Tracks learning progress, skill levels, and personalized notes per student
- **Adaptive Tutoring**: Socratic method chatbot that guides students without giving away answers
- **Performance Tracking**: Evaluates conversations and updates skill levels automatically

## 🏗️ Architecture

### **Clean 4-Agent System** (No Orchestrator)

1. **Initializer** (`agents/initializer.py`)
   - Sets up student sessions and calendar entries
   - Creates default study plans

2. **Questioner** (`agents/questioner.py`)
   - Selects appropriate questions based on date, topics, and skill levels
   - Uses unified database MCP for question retrieval

3. **Chatter** (`agents/chatter.py`)
   - Streaming Socratic tutoring conversations
   - Automatically saves student learning notes via MCP
   - Never gives direct answers - guides discovery

4. **Finalizer** (`agents/finalizer.py`)
   - Analyzes conversation history
   - Evaluates student performance (0-100 scale)
   - Updates skill levels in database

### **Unified Database Layer**

All data now stored in **MySQL** with a single unified MCP server:

**`database/`** folder contains:
- `db.py` - MySQL connection pool manager
- `db_helpers.py` - CRUD operations (students, memory, calendar, skills)
- `db_mcp.py` - Unified MCP server with 6 tools:
  - **Question Bank**: `get_question_by_topic()`, `get_unique_topics()`
  - **Student Data**: `get_skill_level_pairs()`, `get_topics_by_date()`, `add_memory_entry()`, `update_skill_level()`
- `init.py` - Database initialization

**Database Tables:**
- `questions` - Question bank with topic tags and difficulty
- `students` - Student metadata (name, exam)
- `student_memory` - Learning notes and observations
- `calendar_entries` - Study session plans
- `skill_levels` - Topic proficiency scores (0-100)

## 📡 API Endpoints

All endpoints available at `http://localhost:8000`

### `GET /health`
Health check

### `POST /initializer`
Initialize a student session
```json
{
  "student_data": {
    "student_name": "Maria",
    "exam_name": "ENEM 2025",
    "memory": []
  },
  "date": "2025-01-15"
}
```

### `POST /questioner`
Get a question for the student
```json
{
  "student_data": { ... },
  "date": "2025-01-15"
}
```

### `POST /chatter`
Send message to tutoring chatbot
```json
{
  "student_data": { ... },
  "user_message": "I think the answer is...",
  "conversation_history": []
}
```

### `POST /finalizer`
Evaluate session and update skill levels
```json
{
  "student_data": { ... },
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start MySQL
```bash
# Using Docker
docker run -d --name calhacks-mysql \
  -e MYSQL_ROOT_PASSWORD=joe_is_very_cool \
  -p 8003:3306 \
  mysql:8
```

### 3. Run the Server
```bash
# Database initializes automatically on startup
python -m uvicorn main:app --reload
```

Server will display:
```
============================================================
Eigen Coach Backend Starting
============================================================

[Startup] Initializing database connection pool...
[Startup] ✓ Database initialized and ready
[Startup] ✓ API endpoints available

============================================================
Server Ready!
============================================================
```

## 🗂️ Project Structure

```
backend/
├── agents/                     # 4 clean agents
│   ├── chatter.py             # Tutoring chat
│   ├── finalizer.py           # Performance evaluation
│   ├── initializer.py         # Session setup
│   └── questioner.py          # Question selection
├── database/                   # Unified database layer
│   ├── db.py                  # MySQL connection pool
│   ├── db_helpers.py          # CRUD operations
│   ├── db_mcp.py              # Unified MCP server
│   └── init.py                # Initialization
├── migrations/
│   └── 001_create_memory_tables.sql
├── api.py                      # FastAPI endpoints
├── main.py                     # Entry point
└── requirements.txt
```

## 🔧 Configuration

### MySQL Connection
Edit `database/db.py`:
```python
host='localhost'
port=8003
user='root'
password='joe_is_very_cool'
database='calhacks'
```

### MCP Server
Configuration in `.mcp.json`:
```json
{
  "mcpServers": {
    "database": {
      "command": "python3",
      "args": ["-m", "database.db_mcp"]
    }
  }
}
```

## 📊 Database Schema

### Students
- `id`, `student_name`, `exam_name`, `created_at`, `updated_at`

### Questions
- `id`, `question_prompt`, `answer`, `explanation`
- `topic_tag1`, `topic_tag2`, `topic_tag3`
- `difficulty`, `has_been_asked`

### Student Memory
- `id`, `student_id`, `memory_entry`, `created_at`

### Calendar Entries
- `id`, `student_id`, `date`, `topics` (JSON), `n_questions`

### Skill Levels
- `id`, `student_id`, `topic`, `skill_level` (0-100)

## 🎓 Student Skill Scoring

- **0-25**: Novice - Minimal understanding
- **26-50**: Beginner - Basic understanding
- **51-75**: Intermediate - Solid understanding  
- **76-100**: Advanced - Strong mastery

## 📝 Development Notes

- ✅ MySQL for all data (questions + student data)
- ✅ Single unified MCP server for all database operations
- ✅ Connection pooling for performance
- ✅ Automatic migrations on startup
- ✅ Clean agent architecture (no orchestrator)
- ✅ Type-safe with Pydantic models
- ✅ Async/await throughout

## 🤝 Contributing

Built for CalHacks hackathon. Focus on helping Brazilian public school students access quality exam preparation tools.

