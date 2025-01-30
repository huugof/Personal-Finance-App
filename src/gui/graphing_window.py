import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import Database
from models.transaction import Transaction

class GraphingWindow:
    """Window for displaying transaction graphs and projections."""
    
    def __init__(self, parent: ttk.Frame, db: Database):
        """Initialize the graphing window."""
        self.parent = parent
        self.db = db
        self.current_date = datetime.now()
        
        self._setup_ui()
        self._refresh_graphs()
    
    def _setup_ui(self) -> None:
        """Set up the graphing UI."""
        # Create main container
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        
        # Add control panel
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill="x", pady=5)
        
        ttk.Label(control_frame, text="Category:").pack(side="left", padx=5)
        self.category_var = tk.StringVar(value="All Categories")
        self.category_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.category_var, 
            state="readonly"
        )
        self.category_combo.pack(side="left", padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", lambda _: self._refresh_graphs())
        
        # Add refresh button
        ttk.Button(
            control_frame,
            text="Refresh",
            command=self._refresh_graphs
        ).pack(side="right", padx=5)
        
        # Pack the canvas
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _get_monthly_totals(self, transactions: List[Transaction], category: str = None) -> Dict[str, Decimal]:
        """Calculate monthly totals from transactions."""
        monthly_totals: Dict[str, Decimal] = {}
        
        for transaction in transactions:
            if category and transaction.category != category:
                continue
                
            month_key = transaction.date.strftime("%Y-%m")
            if transaction.is_expense:
                monthly_totals[month_key] = monthly_totals.get(month_key, Decimal('0')) - transaction.amount
            else:
                monthly_totals[month_key] = monthly_totals.get(month_key, Decimal('0')) + transaction.amount
        
        return monthly_totals
    
    def _project_future_months(self, num_months: int = 6) -> List[Tuple[str, Decimal]]:
        """Project future months based on budget goals and current spending patterns."""
        # Get budget goals
        budget_goals = self.db.get_budget_goals()
        
        # Calculate monthly net from budget goals
        monthly_budget_net = Decimal('0')
        for category, amount in budget_goals.items():
            # Assume negative for expense categories, positive for income
            if any(tag in self.db.get_category_tags().get(category, "").lower() for tag in ["income", "revenue"]):
                monthly_budget_net += amount
            else:
                monthly_budget_net -= amount
        
        # Start from current month
        projections: List[Tuple[str, Decimal]] = []
        current_date = self.current_date
        running_total = Decimal('0')  # Start from 0 for projection
        
        for i in range(num_months):
            projection_date = current_date + timedelta(days=30*i)
            month_key = projection_date.strftime("%Y-%m")
            running_total += monthly_budget_net
            projections.append((month_key, running_total))
        
        return projections
    
    def _refresh_graphs(self) -> None:
        """Refresh the graphs with current data."""
        self.figure.clear()
        
        # Get transactions for current and last year
        current_year = self.current_date.year
        last_year_transactions = self.db.get_transactions_for_year(current_year - 1)
        this_year_transactions = self.db.get_transactions_for_year(current_year)
        
        # Update category dropdown
        all_categories = {"All Categories"} | {t.category for t in last_year_transactions + this_year_transactions}
        self.category_combo['values'] = sorted(all_categories)
        
        # Get selected category
        selected_category = None if self.category_var.get() == "All Categories" else self.category_var.get()
        
        # Calculate monthly totals
        last_year_totals = self._get_monthly_totals(last_year_transactions, selected_category)
        this_year_totals = self._get_monthly_totals(this_year_transactions, selected_category)
        
        # Create subplot
        ax = self.figure.add_subplot(111)
        
        # Plot last year's data
        last_year_months = sorted(last_year_totals.keys())
        last_year_values = [float(last_year_totals[month]) for month in last_year_months]
        ax.plot(range(len(last_year_months)), last_year_values, 
                label=f"{current_year-1}", marker='o')
        
        # Plot this year's data
        this_year_months = sorted(this_year_totals.keys())
        this_year_values = [float(this_year_totals[month]) for month in this_year_months]
        ax.plot(range(len(this_year_months)), this_year_values, 
                label=str(current_year), marker='o')
        
        # Add projections
        projections = self._project_future_months()
        if projections:
            proj_months = [m for m, _ in projections]
            proj_values = [float(v) for _, v in projections]
            start_idx = len(this_year_months)
            ax.plot(range(start_idx, start_idx + len(proj_months)), 
                   proj_values, 
                   label="Projection", 
                   linestyle='--', 
                   marker='x')
        
        # Customize the plot
        ax.set_title(f"Monthly Net Cash Flow{f' - {selected_category}' if selected_category else ''}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount ($)")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Set x-axis labels
        all_months = sorted(set(last_year_months) | set(this_year_months) | set(m for m, _ in projections))
        ax.set_xticks(range(len(all_months)))
        ax.set_xticklabels([m.split('-')[1] for m in all_months], rotation=45)
        
        # Add horizontal line at y=0
        ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        
        # Adjust layout to prevent label cutoff
        self.figure.tight_layout()
        
        # Refresh canvas
        self.canvas.draw() 