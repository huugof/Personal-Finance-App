from typing import List, Optional, Dict, Tuple
from decimal import Decimal
import anthropic
from models.transaction import Transaction
from database import Database

class AIHandler:
    """Handles AI-powered operations for transaction processing using Claude."""
    
    def __init__(self, api_key: str, db: Database):
        """Initialize the AI handler with Anthropic API key.
        
        Args:
            api_key: The Anthropic API key
            db: Database instance for storing/retrieving data
        """
        self.client = anthropic.Anthropic(
            api_key=api_key
        )
        self.model = "claude-3-haiku-20240307"  # Using Claude 3 Haiku
        self.db = db
    
    def suggest_category(self, description: str, amount: Decimal) -> str:
        """Use Claude to suggest a category based on transaction description and amount."""
        try:
            # Get existing categories for context
            categories = self.db.get_all_categories()
            
            prompt = (
                "As a financial expert, categorize this transaction. Choose from the existing categories "
                "or suggest 'Uncategorized' if none fit well. Respond with ONLY the category name, nothing else.\n\n"
                f"Transaction Description: {description}\n"
                f"Amount: ${amount}\n"
                f"Available Categories: {', '.join(categories)}"
            )
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            suggested_category = response.content[0].text.strip()
            return suggested_category if suggested_category in categories else "Uncategorized"
            
        except Exception as e:
            print(f"AI categorization error: {e}")
            return "Uncategorized"
    
    def generate_rules(self, transactions: List[Transaction]) -> List[Tuple[str, str, Optional[Decimal]]]:
        """Analyze transactions to suggest categorization rules."""
        try:
            # Group similar transactions
            transaction_patterns = {}
            for t in transactions:
                key_words = ' '.join(word for word in t.description.split() if len(word) > 3)
                if key_words in transaction_patterns:
                    transaction_patterns[key_words].append(t)
                else:
                    transaction_patterns[key_words] = [t]
            
            # Find patterns with consistent categorization
            rules = []
            for pattern, similar_transactions in transaction_patterns.items():
                if len(similar_transactions) >= 2:  # Only suggest rules for repeated patterns
                    categories = {t.category for t in similar_transactions}
                    amounts = {t.amount for t in similar_transactions}
                    
                    if len(categories) == 1:  # Consistent categorization
                        category = categories.pop()
                        amount = amounts.pop() if len(amounts) == 1 else None
                        
                        # Use Claude to validate and refine the pattern
                        prompt = (
                            "Given this transaction pattern, suggest a refined search pattern that would reliably "
                            "match similar transactions. Return ONLY the pattern, nothing else.\n\n"
                            f"Original Pattern: {pattern}\n"
                            f"Sample Transactions:\n" + 
                            "\n".join(t.description for t in similar_transactions[:3])
                        )
                        
                        response = self.client.messages.create(
                            model=self.model,
                            max_tokens=50,
                            temperature=0.3,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        refined_pattern = response.content[0].text.strip()
                        rules.append((refined_pattern, category, amount))
            
            return rules
            
        except Exception as e:
            print(f"Rule generation error: {e}")
            return []
    
    def analyze_spending_patterns(self) -> Dict[str, List[str]]:
        """Analyze spending patterns and provide insights."""
        try:
            transactions = self.db.get_transactions()
            
            # Prepare transaction summary
            categories = set(t.category for t in transactions)
            date_range = f"{min(t.date for t in transactions)} to {max(t.date for t in transactions)}"
            
            # Calculate category totals
            category_totals = {}
            for t in transactions:
                if not t.ignored:
                    category_totals[t.category] = category_totals.get(t.category, Decimal('0')) + t.amount
            
            prompt = (
                "Analyze these transaction patterns and provide 3 key insights about spending habits. "
                "Format as a bullet-point list.\n\n"
                f"Total Transactions: {len(transactions)}\n"
                f"Date Range: {date_range}\n"
                "Category Totals:\n" +
                "\n".join(f"- {cat}: ${total:,.2f}" for cat, total in category_totals.items())
            )
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            insights = [line.strip() for line in response.content[0].text.split("\n") if line.strip()]
            return {"insights": insights}
            
        except Exception as e:
            print(f"Analysis error: {e}")
            return {"insights": ["Analysis unavailable"]} 