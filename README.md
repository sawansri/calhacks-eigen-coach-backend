# calhacks-eigen-coach-backend

AI powered tutor for exam prep, backstory is that in Brazilian public schools, students don't have the resources to hire private tutors and the exams are too obscure to be featured on websites like KhanAcademy. Our app essentially provides this platform, all users have to do is upload papers and our agents will create a time-aware study guide, with a question bank, flexible question generating, and memory to store progress by topic

## Time-awareness --> study timeline

## Question Bank --> tags and topics

### VectorDB (ChromaDB)

#### Pre-processing before vectorizing in DB
Need LLM to process exams, extracting exam type, labelling each question by topic (tagging them basically)

## Flexible --> no pre-designing, generate on the go

## Memory --> progress tracking by topic




Agentic Architecture powered by Claude Agent SDK in Python (https://docs.claude.com/en/api/agent-sdk/python)

Lead Tutor Agent (The Orchestrator): This is the "brain" the user talks to. It maintains the conversational state and decides which specialist to call.

Study Plan Agent (Time-Awareness): This agent manages the "study timeline." Its only job is to look at the user's goals and progress and answer the question: "What should we study right now?"

Question Bank Agent (Retrieval): This agent interfaces directly with ChromaDB. Its job is to fetch existing questions based on specific criteria (e.g., "Get me 3 'Medium' questions on 'Kinematics'").

Explanation Agent (Flexible Generation): This agent interfaces with Claude (your LLM) and ChromaDB. It uses Retrieval-Augmented Generation (RAG) to create new content, whether that's a new question or a detailed explanation.
