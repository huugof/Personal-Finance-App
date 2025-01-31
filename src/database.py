import sqlite3
from typing import List, Optional, Dict, Set, Tuple
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
            
            # Add after the existing table creations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorization_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    FOREIGN KEY (category) REFERENCES categories(name)
                )
            """)
            
            # Check if we need to add the ignored column
            cursor.execute("PRAGMA table_info(transactions)")
            columns = {column[1]: column for column in cursor.fetchall()}
            
            if 'ignored' not in columns:
                print("Adding ignored column to transactions table")
                cursor.execute("ALTER TABLE transactions ADD COLUMN ignored BOOLEAN DEFAULT 0")
            
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
        """Get all transactions from the database."""
        print("Debug: Fetching transactions from database")  # Debug print
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, amount, description, category, transaction_type, ignored 
                FROM transactions 
                ORDER BY date DESC
            """)
            rows = cursor.fetchall()
            print(f"Debug: Found {len(rows)} rows in database")  # Debug print
            return [
                Transaction(
                    id=row[0],
                    date=datetime.strptime(row[1], "%Y-%m-%dT%H:%M:%S"),
                    amount=Decimal(str(row[2])),
                    description=row[3],
                    category=row[4],
                    transaction_type=row[5],
                    ignored=bool(row[6])
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
                AND (ignored = 0 OR ignored IS NULL)
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

    def get_all_categories(self) -> List[str]:
        """Get all category names from the database.
        
        Returns:
            List of category names sorted alphabetically
        """
        print("Debug: Fetching all categories")  # Debug print
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get categories from categories table
            cursor.execute("SELECT DISTINCT name FROM categories WHERE name IS NOT NULL")
            category_names = set(row[0] for row in cursor.fetchall())
            
            # Get categories from transactions table
            cursor.execute("SELECT DISTINCT category FROM transactions WHERE category IS NOT NULL")
            transaction_categories = set(row[0] for row in cursor.fetchall())
            
            # Combine both sets and remove empty strings
            all_categories = category_names | transaction_categories
            all_categories = {cat for cat in all_categories if cat and cat.strip()}
            
            print(f"Debug: Found categories: {all_categories}")  # Debug print
            return sorted(all_categories)

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
                SELECT id, date, amount, description, category, transaction_type, ignored 
                FROM transactions 
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
                    transaction_type=row[5],
                    ignored=bool(row[6])
                )
                for row in cursor.fetchall()
            ]

    def get_transactions_for_year(self, year: int) -> List[Transaction]:
        """Get all transactions for a specific year.
        
        Args:
            year: The target year
            
        Returns:
            List of transactions for that year
        """
        start_date = datetime(year, 1, 1).isoformat()
        end_date = datetime(year + 1, 1, 1).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, amount, description, category, transaction_type, ignored 
                FROM transactions 
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
                    transaction_type=row[5],
                    ignored=bool(row[6])
                )
                for row in cursor.fetchall()
            ] 

    def update_transaction_category(self, transaction_id: int, new_category: str) -> None:
        """Update the category of a transaction.
        
        Args:
            transaction_id: The ID of the transaction to update
            new_category: The new category name
        
        Raises:
            Exception: If the update fails
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # First ensure the category exists in categories table
                conn.execute("""
                    INSERT OR IGNORE INTO categories (name)
                    VALUES (?)
                """, (new_category,))
                
                # Then update the transaction
                conn.execute("""
                    UPDATE transactions 
                    SET category = ? 
                    WHERE id = ?
                """, (new_category, transaction_id))
                
        except sqlite3.Error as e:
            raise Exception(f"Failed to update transaction category: {str(e)}") 

    def add_categorization_rule(self, pattern: str, category: str, priority: int = 0) -> None:
        """Add a new categorization rule.
        
        Args:
            pattern: Text pattern to match in transaction description
            category: Category to assign when pattern matches
            priority: Rule priority (higher numbers take precedence)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO categorization_rules (pattern, category, priority)
                VALUES (?, ?, ?)
            """, (pattern, category, priority))

    def get_categorization_rules(self) -> List[Tuple[str, str, int]]:
        """Get all categorization rules.
        
        Returns:
            List of tuples containing (pattern, category, priority)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pattern, category, priority 
                FROM categorization_rules 
                ORDER BY priority DESC
            """)
            return cursor.fetchall()

    def delete_categorization_rule(self, pattern: str, category: str) -> None:
        """Delete a categorization rule.
        
        Args:
            pattern: Pattern to match
            category: Category to assign
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM categorization_rules 
                WHERE pattern = ? AND category = ?
            """, (pattern, category))

    def auto_categorize_transaction(self, description: str) -> Optional[str]:
        """Determine category based on transaction description and rules.
        
        Args:
            description: Transaction description to categorize
            
        Returns:
            Matching category or None if no rules match
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Escape special characters in the description
            escaped_description = description.replace('%', '\\%').replace('_', '\\_')
            cursor.execute("""
                SELECT category FROM categorization_rules 
                WHERE ? LIKE '%' || replace(replace(pattern, '%', '\\%'), '_', '\\_') || '%'
                ORDER BY priority DESC
                LIMIT 1
            """, (escaped_description,))
            result = cursor.fetchone()
            return result[0] if result else None

    def apply_rules_to_existing_transactions(self) -> Tuple[int, int]:
        """Apply categorization rules to all existing transactions.
        
        Returns:
            Tuple of (number of transactions updated, total transactions processed)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all transactions
            cursor.execute("SELECT id, description, category FROM transactions")
            transactions = cursor.fetchall()
            
            updated_count = 0
            total_count = len(transactions)
            
            for trans_id, description, current_category in transactions:
                # Skip transactions that already have a non-Uncategorized category
                if current_category and current_category != "Uncategorized":
                    continue
                    
                # Try to find a matching rule
                new_category = self.auto_categorize_transaction(description)
                if new_category and new_category != current_category:
                    cursor.execute(
                        "UPDATE transactions SET category = ? WHERE id = ?",
                        (new_category, trans_id)
                    )
                    updated_count += 1
            
            conn.commit()
            return (updated_count, total_count) 