from database import Database
from gui.main_window import MainWindow
import os
from dotenv import load_dotenv

def main():
    """Main entry point for the budget tracker application."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment variable
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not claude_api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    
    db_path = os.getenv("DB_PATH", "budget.db")
    
    try:
        db = Database(db_path, api_key=claude_api_key)
        app = MainWindow(db)
        app.run()
    except Exception as e:
        print(f"Error initializing application: {str(e)}")
        raise

if __name__ == "__main__":
    main() 