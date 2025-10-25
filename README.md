# calhacks-eigen-coach-backend

AI powered tutor for exam prep, backstory is that in Brazilian public schools, students don't have the resources to hire private tutors and the exams are too obscure to be featured on websites like KhanAcademy. Our app essentially provides this platform, all users have to do is upload papers and our agents will create a time-aware study guide, with a question bank, flexible question generating, and memory to store progress by topic

## Time-awareness --> study timeline
Question Bank Agent determines tags/question topics, use math/algorithms + sensible study defaults (hours per day, etc) to come up with a plan, no llm needed here

## Question Bank --> tags and topics
Question Bank Agent processes exam, determines exam, determines topics per exam

### VectorDB (ChromaDB)

#### Pre-processing before vectorizing in DB
Need LLM to process exams, extracting exam type, labelling each question by topic (tagging them basically)

## Flexible --> no pre-designing, generate on the go

## Memory --> progress tracking by topic




## Agentic Architecture powered by Claude Agent SDK in Python (https://docs.claude.com/en/api/agent-sdk/python)

Data Sources

User uploads

Official resources

Other info?

Topic explanations?

RAG Layer (Knowledge Base)

Extracted questions (tagged)

Proctoring guidelines, etc.

Features

Study timeline

Tags and topics (question bank)

No pre-designing

Track progress

User State (Stored in user_state.json)

Single JSON file (e.g., user_state.json) to store all persistent user data.

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

Outputs: Docs and labeled data (to be stored in ChromaDB).

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

ChromaDB

Stores the vector-indexed knowledge base (extracted questions, guidelines, etc.).

Used by the RAG Layer.

JSON File (user_state.json)

Stores all user-specific data (preferences, progress, etc.).

Used by the Orchestrator, Planner, and Grader agents.
