from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

@dataclass
class Transaction:
    """Represents a single financial transaction."""
    
    id: Optional[int]
    date: datetime
    amount: Decimal
    description: str
    category: str
    transaction_type: str  # "income" or "expense"
    ignored: bool = False  # New field with default False
    
    @property
    def is_expense(self) -> bool:
        """Check if the transaction is an expense."""
        return self.transaction_type.lower() == "expense" and not self.ignored
    
    @property
    def is_income(self) -> bool:
        """Check if the transaction is income."""
        return self.transaction_type.lower() == "income" and not self.ignored 