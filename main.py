import sys
from question_bank.qb import initialize_database

def main():
    """Main entry point to launch all backend instances"""
    print("Starting Calhacks Backend Services...")
    
    # Initialize database
    print("\n[1/3] Initializing Database...")
    initialize_database()
    
    # TODO: Add other service instances here
    print("\n[2/3] Starting API Server...")
    # api_instance = start_api_server()
    
    print("\n[3/3] Starting Additional Services...")
    # other_instance = start_other_services()
    
    print("\nAll services started successfully!")

if __name__ == "__main__":
    main()