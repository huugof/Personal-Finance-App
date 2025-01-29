from database import Database
from gui.main_window import MainWindow

def main():
    """Main entry point for the budget tracker application."""
    db = Database()
    app = MainWindow(db)
    app.run()

if __name__ == "__main__":
    main() 