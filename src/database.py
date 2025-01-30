import sqlite3
from typing import List, Optional, Dict, Set
from datetime import datetime
from decimal import Decimal
from models.transaction import Transaction

class Database:
    """Handles all database operations for the budget tracker."""
    
    def __init__(self, db_path: str = "data/budget.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create necessary database tables if they don't exist."""
        print("Creating/updating database tables")  # Debug log
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    transaction_type TEXT NOT NULL
                )
            """)
            
            # Create or update categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    name TEXT PRIMARY KEY,
                    budget_goal DECIMAL(10,2),
                    tags TEXT DEFAULT ''
                )
            """)
            
            # Check if we need to migrate tags column
            cursor.execute("PRAGMA table_info(categories)")
            columns = {column[1]: column for column in cursor.fetchall()}
            
            if 'tags' not in columns:
                print("Adding tags column to categories table")
                cursor.execute("ALTER TABLE categories ADD COLUMN tags TEXT DEFAULT ''")
            
            conn.commit()
    
    def add_transaction(self, transaction: Transaction) -> int:
        """Add a new transaction to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (date, amount, description, category, transaction_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                transaction.date.isoformat(),
                str(transaction.amount),
                transaction.description,
                transaction.category,
                transaction.transaction_type
            ))
            return cursor.lastrowid
    
    def get_transactions(self) -> List[Transaction]:
        """Retrieve all transactions from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions")
            rows = cursor.fetchall()
            return [
                Transaction(
                    id=row[0],
                    date=datetime.fromisoformat(row[1]),
                    amount=Decimal(row[2]),
                    description=row[3],
                    category=row[4],
                    transaction_type=row[5]
                )
                for row in rows
            ]
    
    def get_category_totals(self) -> Dict[str, Decimal]:
        """Get total spending by category."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, SUM(amount) 
                FROM transactions 
                WHERE transaction_type = 'expense'
                GROUP BY category
            """)
            return {row[0]: Decimal(row[1]) for row in cursor.fetchall()}

    def set_budget_goal(self, category: str, amount: Decimal) -> None:
        """Set or update a budget goal for a category.
        
        Args:
            category: The category name
            amount: The budget goal amount
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO categories (name, budget_goal)
                VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET budget_goal = ?
            """, (category, str(amount), str(amount)))

    def get_budget_goals(self) -> Dict[str, Decimal]:
        """Get all budget goals.
        
        Returns:
            Dict mapping category names to their budget goals
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, budget_goal FROM categories WHERE budget_goal IS NOT NULL")
            return {row[0]: Decimal(row[1]) for row in cursor.fetchall()}

    def get_budget_goal(self, category: str) -> Optional[Decimal]:
        """Get budget goal for a specific category.
        
        Args:
            category: The category name
            
        Returns:
            The budget goal amount or None if not set
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT budget_goal FROM categories WHERE name = ?", (category,))
            row = cursor.fetchone()
            return Decimal(row[0]) if row and row[0] is not None else None

    def debug_print_categories(self) -> None:
        """Print all categories table data for debugging."""
        print("\n=== DEBUG: Categories Table Contents ===")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, budget_goal, tags FROM categories")
            rows = cursor.fetchall()
            for row in rows:
                print(f"Category: {row[0]}")
                print(f"  Budget Goal: {row[1]}")
                print(f"  Tags: {row[2]}")
            print("=====================================\n")

    def set_category_tags(self, category: str, tags: str) -> None:
        """Set or update tags for a category.
        
        Args:
            category: The category name
            tags: Comma-separated tags
        """
        print(f"Setting tags for {category}: {tags}")  # Debug log
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # First ensure the category exists with all fields
            cursor.execute("""
                INSERT INTO categories (name, budget_goal, tags)
                VALUES (?, NULL, ?)
                ON CONFLICT(name) DO UPDATE SET 
                tags = CASE 
                    WHEN excluded.tags != '' THEN excluded.tags 
                    ELSE categories.tags 
                END
            """, (category, tags))
            conn.commit()
            
            # Debug verification
            cursor.execute("SELECT tags FROM categories WHERE name = ?", (category,))
            result = cursor.fetchone()
            print(f"Verified tags for {category}: {result[0] if result else None}")  # Debug log

    def get_category_tags(self) -> Dict[str, str]:
        """Get all category tags.
        
        Returns:
            Dict mapping category names to their tags
        """
        print("Retrieving all category tags")  # Debug log
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Changed query to include all tags, even NULL ones
            cursor.execute("SELECT name, COALESCE(tags, '') as tags FROM categories")
            results = {row[0]: row[1] for row in cursor.fetchall() if row[1]}  # Only include non-empty tags
            print(f"Retrieved tags: {results}")  # Debug log
            return results

    def add_category(self, category: str) -> None:
        """Add a new category to the database.
        
        Args:
            category: The category name to add
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name)
                VALUES (?)
            """, (category,))
            conn.commit()

    def get_all_categories(self) -> Set[str]:
        """Get all category names from both transactions and categories tables.
        
        Returns:
            Set of unique category names
        """
        print("Getting all categories")  # Debug log
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get categories from transactions
            cursor.execute("SELECT DISTINCT category FROM transactions")
            transaction_categories = {row[0] for row in cursor.fetchall()}
            
            # Get categories from categories table
            cursor.execute("SELECT name FROM categories")
            defined_categories = {row[0] for row in cursor.fetchall()}
            
            # Combine both sets
            all_categories = transaction_categories | defined_categories
            print(f"Found categories: {all_categories}")  # Debug log
            return all_categories

    def delete_category(self, category: str) -> None:
        """Delete a category from the database.
        
        Args:
            category: The category name to delete
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE name = ?", (category,))
            conn.commit()

    def delete_transaction(self, transaction_id: int) -> None:
        """Delete a transaction from the database.
        
        Args:
            transaction_id: The ID of the transaction to delete
        """
        print(f"Deleting transaction with ID: {transaction_id}")  # Debug log
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            transaction = cursor.fetchone()
            print(f"Found transaction to delete: {transaction}")  # Debug log
            
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            rows_affected = cursor.rowcount
            conn.commit()
            print(f"Rows affected by delete: {rows_affected}")  # Debug log 

    def get_transactions_for_month(self, date: datetime) -> List[Transaction]:
        """Get all transactions for a specific month.
        
        Args:
            date: Any date in the target month
            
        Returns:
            List of transactions for that month
        """
        start_date = date.replace(day=1).isoformat()
        if date.month == 12:
            end_date = date.replace(year=date.year + 1, month=1, day=1).isoformat()
        else:
            end_date = date.replace(month=date.month + 1, day=1).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE date >= ? AND date < ?
                ORDER BY date
            """, (start_date, end_date))
            
            return [
                Transaction(
                    id=row[0],
                    date=datetime.fromisoformat(row[1]),
                    amount=Decimal(row[2]),
                    description=row[3],
                    category=row[4],
                    transaction_type=row[5]
                )
                for row in cursor.fetchall()
            ] 