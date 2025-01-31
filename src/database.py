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
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if we need to update the categorization_rules table
            cursor.execute("PRAGMA table_info(categorization_rules)")
            columns = {col[1] for col in cursor.fetchall()}
            
            if "amount" not in columns:
                # Backup existing rules
                cursor.execute("SELECT pattern, category, priority FROM categorization_rules")
                existing_rules = cursor.fetchall()
                
                # Drop and recreate table
                cursor.execute("DROP TABLE categorization_rules")
                cursor.execute("""
                    CREATE TABLE categorization_rules (
                        pattern TEXT NOT NULL,
                        category TEXT NOT NULL,
                        amount DECIMAL,
                        amount_tolerance DECIMAL DEFAULT 0.01,
                        priority INTEGER DEFAULT 0,
                        PRIMARY KEY (pattern, category)
                    )
                """)
                
                # Restore existing rules
                cursor.executemany("""
                    INSERT INTO categorization_rules (pattern, category, priority)
                    VALUES (?, ?, ?)
                """, existing_rules)
            
            # Create other tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount DECIMAL NOT NULL,
                    description TEXT,
                    category TEXT,
                    transaction_type TEXT NOT NULL,
                    ignored BOOLEAN DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    name TEXT PRIMARY KEY,
                    budget_goal DECIMAL,
                    tags TEXT
                )
            """)
            
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

    def update_transaction_by_attributes(
        self,
        date: datetime,
        amount: Decimal,
        description: str,
        category: str,
        transaction_type: str
    ) -> None:
        """Update a transaction's category based on its attributes.
        
        Args:
            date: Transaction date
            amount: Transaction amount
            description: Transaction description
            category: New category to set
            transaction_type: Type of transaction (income/expense)
            
        Raises:
            Exception: If the update fails
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # First ensure the category exists in categories table
                conn.execute("""
                    INSERT OR IGNORE INTO categories (name)
                    VALUES (?)
                """, (category,))
                
                # Then update the transaction
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE transactions 
                    SET category = ? 
                    WHERE date = ? 
                    AND amount = ? 
                    AND description = ? 
                    AND transaction_type = ?
                """, (
                    category,
                    date.strftime("%Y-%m-%dT%H:%M:%S"),  # Convert datetime to string
                    str(amount),  # Convert Decimal to string
                    description,
                    transaction_type
                ))
                
                if cursor.rowcount == 0:
                    raise Exception("No matching transaction found")
                
                conn.commit()
                
        except sqlite3.Error as e:
            raise Exception(f"Failed to update transaction category: {str(e)}")

    def add_categorization_rule(
        self, 
        pattern: str, 
        category: str, 
        amount: Optional[Decimal] = None,
        tolerance: Decimal = Decimal("0.01"),
        priority: int = 0
    ) -> None:
        """Add a new categorization rule.
        
        Args:
            pattern: The pattern to match against transaction descriptions
            category: The category to assign
            amount: Optional specific amount to match
            tolerance: Amount tolerance (default $0.01)
            priority: Rule priority (higher numbers run first)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO categorization_rules 
                (pattern, category, amount, amount_tolerance, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (pattern, category, amount, tolerance, priority))
            conn.commit()

    def get_categorization_rules(self) -> List[Tuple[str, str, Optional[Decimal], Decimal, int]]:
        """Get all categorization rules.
        
        Returns:
            List of tuples containing (pattern, category, amount, tolerance, priority)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pattern, category, amount, amount_tolerance, priority 
                FROM categorization_rules 
                ORDER BY priority DESC
            """)
            
            # Convert amount and tolerance strings to Decimal if not None
            rules = []
            for row in cursor.fetchall():
                pattern, category, amount_str, tolerance_str, priority = row
                amount = Decimal(amount_str) if amount_str is not None else None
                tolerance = Decimal(tolerance_str) if tolerance_str is not None else Decimal("0.01")
                rules.append((pattern, category, amount, tolerance, priority))
            
            return rules

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

    def apply_rules_to_existing_transactions(self) -> None:
        """Apply categorization rules to all transactions.
        
        This method will:
        1. Get all transactions
        2. Get all categorization rules ordered by priority
        3. For each transaction, apply the first matching rule
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all transactions (removed the category filter)
            cursor.execute("""
                SELECT id, description, amount, date, transaction_type 
                FROM transactions
            """)
            transactions = cursor.fetchall()
            
            # Get all rules ordered by priority
            cursor.execute("""
                SELECT pattern, category, amount, amount_tolerance, priority 
                FROM categorization_rules 
                ORDER BY priority DESC
            """)
            rules = cursor.fetchall()
            
            # Process each transaction
            updates_made = 0
            for trans_id, description, trans_amount, date, trans_type in transactions:
                for pattern, category, rule_amount, tolerance, priority in rules:
                    # Check if description matches pattern
                    if pattern.lower() in description.lower():
                        # If rule has an amount, check if it matches within tolerance
                        if rule_amount is not None:
                            rule_amount = Decimal(str(rule_amount))
                            tolerance = Decimal(str(tolerance or "0.01"))
                            trans_amount = Decimal(str(trans_amount))
                            
                            if abs(trans_amount - rule_amount) > tolerance:
                                continue  # Amount doesn't match within tolerance
                        
                        # Update the transaction with the matching category
                        cursor.execute("""
                            UPDATE transactions 
                            SET category = ? 
                            WHERE id = ?
                        """, (category, trans_id))
                        updates_made += 1
                        break  # Stop checking rules for this transaction
            
            conn.commit()
            print(f"Updated {updates_made} transactions")  # Debug log

    def delete_transaction_by_attributes(
        self,
        date: str,
        amount: str,
        description: str,
        category: str,
        transaction_type: str
    ) -> None:
        """Delete a transaction that matches all the given attributes.
        
        Args:
            date: The transaction date in ISO format (YYYY-MM-DDT00:00:00)
            amount: The transaction amount as a string
            description: The transaction description
            category: The transaction category
            transaction_type: The type of transaction (income/expense)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM transactions 
                WHERE date = ? 
                AND amount = ? 
                AND description = ? 
                AND category = ? 
                AND transaction_type = ?
            """, (
                date,
                amount,
                description,
                category,
                transaction_type
            ))
            conn.commit() 