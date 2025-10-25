import json
from src.orchestrator_agent import OrchestratorAgent
from src.document_ingestion_agent import DocumentIngestionAgent
from src.planner_agent import PlannerAgent
from src.tutor_agent import TutorAgent
from src.feedback_agent import FeedbackAgent
from src.scraper_agent import ScraperAgent

def main():
    # Load user state
    with open("user_state.json", "r") as f:
        user_state = json.load(f)

    # Initialize agents
    orchestrator = OrchestratorAgent()
    doc_ingestion = DocumentIngestionAgent()
    planner = PlannerAgent()
    tutor = TutorAgent()
    feedback = FeedbackAgent()
    scraper = ScraperAgent()

    # Example usage
    user_query = "I want to study math."
    response = orchestrator(user_query=user_query)
    print(response)

    document_path = "/path/to/your/document.pdf"
    response = doc_ingestion(document_path=document_path)
    print(response)

    response = planner(user_preferences=user_state["user_preferences"])
    print(response)

    response = tutor(topic="algebra")
    print(response)

    response = feedback(user_answer="2x", correct_answer="2x")
    print(response)

    response = scraper(query="calculus practice problems")
    print(response)

if __name__ == "__main__":
    main()