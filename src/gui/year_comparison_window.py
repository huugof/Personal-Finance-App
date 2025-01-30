import tkinter as tk
from tkinter import ttk
from datetime import datetime
from decimal import Decimal
from typing import Dict, List
from database import Database
from models.transaction import Transaction

class YearComparisonWindow:
    """Window for comparing spending between years."""
    
    def __init__(self, parent: ttk.Frame, db: Database):
        """Initialize the year comparison window."""
        self.parent = parent
        self.db = db
        self.current_year = datetime.now().year
        
        # Initialize UI components
        self._setup_ui()
        self._refresh_comparison()
    
    def _setup_ui(self) -> None:
        """Set up the comparison UI."""
        # Create the main frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create Treeview for comparison
        self.tree = ttk.Treeview(
            self.frame,
            columns=("Category", "Last Year", "This Year", "Difference", "% Change"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.tree.heading("Category", text="Category")
        self.tree.heading("Last Year", text=f"{self.current_year - 1}")
        self.tree.heading("This Year", text=str(self.current_year))
        self.tree.heading("Difference", text="Difference")
        self.tree.heading("% Change", text="% Change")
        
        # Set column widths
        for col in self.tree["columns"]:
            self.tree.column(col, width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack components
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Total summary frame
        summary_frame = ttk.LabelFrame(self.parent, text="Total Summary")
        summary_frame.pack(fill="x", padx=10, pady=5)
        
        self.total_last_year = ttk.Label(summary_frame, text="Last Year Total: $0.00")
        self.total_last_year.pack(side="left", padx=20)
        
        self.total_this_year = ttk.Label(summary_frame, text="This Year Total: $0.00")
        self.total_this_year.pack(side="left", padx=20)
        
        self.total_difference = ttk.Label(summary_frame, text="Difference: $0.00")
        self.total_difference.pack(side="left", padx=20)
        
        self.total_percent = ttk.Label(summary_frame, text="% Change: 0%")
        self.total_percent.pack(side="left", padx=20)
    
    def _calculate_category_totals(self, transactions: List[Transaction]) -> Dict[str, Decimal]:
        """Calculate total spending by category from transactions."""
        totals: Dict[str, Decimal] = {}
        for transaction in transactions:
            if transaction.is_expense:  # Only include expenses
                totals[transaction.category] = totals.get(transaction.category, Decimal('0')) + transaction.amount
        return totals
    
    def _refresh_comparison(self) -> None:
        """Refresh the year comparison display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get transactions for both years
        last_year_transactions = self.db.get_transactions_for_year(self.current_year - 1)
        this_year_transactions = self.db.get_transactions_for_year(self.current_year)
        
        # Calculate totals by category
        last_year_totals = self._calculate_category_totals(last_year_transactions)
        this_year_totals = self._calculate_category_totals(this_year_transactions)
        
        # Get all unique categories
        all_categories = set(last_year_totals.keys()) | set(this_year_totals.keys())
        
        # Calculate grand totals
        total_last_year = sum(last_year_totals.values())
        total_this_year = sum(this_year_totals.values())
        
        # Add rows for each category
        for category in sorted(all_categories):
            last_year_amount = last_year_totals.get(category, Decimal('0'))
            this_year_amount = this_year_totals.get(category, Decimal('0'))
            difference = this_year_amount - last_year_amount
            
            # Calculate percentage change
            if last_year_amount != 0:
                percent_change = (difference / last_year_amount) * 100
                percent_str = f"{percent_change:+.1f}%"
            else:
                percent_str = "N/A"
            
            self.tree.insert("", "end", values=(
                category,
                f"${last_year_amount:,.2f}",
                f"${this_year_amount:,.2f}",
                f"${difference:+,.2f}",
                percent_str
            ))
        
        # Update summary labels
        difference = total_this_year - total_last_year
        percent_change = ((total_this_year / total_last_year) - 1) * 100 if total_last_year != 0 else 0
        
        self.total_last_year.config(text=f"Last Year Total: ${total_last_year:,.2f}")
        self.total_this_year.config(text=f"This Year Total: ${total_this_year:,.2f}")
        self.total_difference.config(text=f"Difference: ${difference:+,.2f}")
        self.total_percent.config(text=f"% Change: {percent_change:+.1f}%") 