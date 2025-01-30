import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Set, Dict, Optional, List, Tuple
from database import Database
import decimal
from datetime import datetime

class BudgetGoalsWindow:
    """Window for managing category budget goals."""
    
    def __init__(self, parent: ttk.Frame, db: Database) -> None:
        """Initialize the budget goals window."""
        self.parent = parent
        self.db = db
        self.category_entries: Dict[str, Tuple[ttk.Entry, ttk.Entry]] = {}
        
        # Initialize sort variables
        self.sort_var = tk.StringVar(value="name")
        self.sort_direction_var = tk.StringVar(value="asc")
        
        # Set up the UI components
        self._setup_ui()
        
        # Initial refresh of categories
        self._refresh_categories()
    
    def _setup_ui(self) -> None:
        """Set up the budget goals UI."""
        # Create totals frame and labels
        totals_frame = ttk.LabelFrame(self.parent, text="Budget Summary")
        totals_frame.pack(fill="x", padx=10, pady=5)

        # Budget Summary (First Row)
        budget_frame = ttk.Frame(totals_frame)
        budget_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(budget_frame, text="Budget Goals:", font=("", 10, "bold")).pack(side="left", padx=5)
        self.budget_income_label = ttk.Label(budget_frame, text="Income: $0.00")
        self.budget_income_label.pack(side="left", padx=20)
        
        self.budget_expense_label = ttk.Label(budget_frame, text="Expenses: $0.00")
        self.budget_expense_label.pack(side="left", padx=20)
        
        self.budget_balance_label = ttk.Label(budget_frame, text="Balance: $0.00")
        self.budget_balance_label.pack(side="left", padx=20)

        # Actual Summary (Second Row)
        actual_frame = ttk.Frame(totals_frame)
        actual_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(actual_frame, text="Current Month:", font=("", 10, "bold")).pack(side="left", padx=5)
        self.actual_income_label = ttk.Label(actual_frame, text="Income: $0.00")
        self.actual_income_label.pack(side="left", padx=20)
        
        self.actual_expense_label = ttk.Label(actual_frame, text="Expenses: $0.00")
        self.actual_expense_label.pack(side="left", padx=20)
        
        self.actual_balance_label = ttk.Label(actual_frame, text="Balance: $0.00")
        self.actual_balance_label.pack(side="left", padx=20)

        # Add new category frame
        new_category_frame = ttk.Frame(self.parent)
        new_category_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(new_category_frame, text="New Category:").pack(side="left", padx=5)
        self.new_category_entry = ttk.Entry(new_category_frame)
        self.new_category_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(
            new_category_frame,
            text="Add Category",
            command=self._add_new_category
        ).pack(side="left", padx=5)

        # Sort controls frame
        sort_frame = ttk.LabelFrame(self.parent, text="Sort Options")
        sort_frame.pack(fill="x", padx=10, pady=5)

        # Sort by options
        sort_by_frame = ttk.Frame(sort_frame)
        sort_by_frame.pack(side="left", padx=5, pady=5)

        ttk.Label(sort_by_frame, text="Sort by:").pack(side="left", padx=5)
        for text, value in [("Name", "name"), ("Goal", "goal"), ("Tags", "tags")]:
            ttk.Radiobutton(
                sort_by_frame,
                text=text,
                variable=self.sort_var,
                value=value,
                command=self._refresh_categories
            ).pack(side="left", padx=5)

        # Direction options
        direction_frame = ttk.Frame(sort_frame)
        direction_frame.pack(side="right", padx=5, pady=5)

        ttk.Label(direction_frame, text="Order:").pack(side="left", padx=5)
        for text, value in [("Ascending", "asc"), ("Descending", "desc")]:
            ttk.Radiobutton(
                direction_frame,
                text=text,
                variable=self.sort_direction_var,
                value=value,
                command=self._refresh_categories
            ).pack(side="left", padx=5)

        # Create scrollable frame for categories
        self.canvas = tk.Canvas(self.parent)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure grid columns in scrollable frame
        self.scrollable_frame.grid_columnconfigure(1, weight=1, minsize=150)  # Goal column
        self.scrollable_frame.grid_columnconfigure(2, weight=1, minsize=200)  # Tags column
        self.scrollable_frame.grid_columnconfigure(3, minsize=50)  # Delete button column
        
        # Headers
        ttk.Label(self.scrollable_frame, text="Category", font=("", 10, "bold"), width=20).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        ttk.Label(self.scrollable_frame, text="Monthly Goal ($)", font=("", 10, "bold"), width=15).grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        ttk.Label(self.scrollable_frame, text="Tags", font=("", 10, "bold"), width=30).grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        
        # Configure canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Save Button
        ttk.Button(
            self.parent,
            text="Save All Goals",
            command=self._save_all_goals
        ).pack(pady=10)
    
    def _add_new_category(self) -> None:
        """Add a new category to the list."""
        new_category = self.new_category_entry.get().strip()
        if not new_category:
            messagebox.showerror("Error", "Please enter a category name")
            return
            
        if new_category in self.category_entries:
            messagebox.showerror("Error", "Category already exists")
            return
            
        # Add to database first
        self.db.add_category(new_category)
        self._add_category_row(new_category)
        self.new_category_entry.delete(0, tk.END)
    
    def _add_category_row(self, category: str, goal: Optional[Decimal] = None, tags: str = "") -> None:
        """Add a row for a category in the scrollable frame."""
        row = len(self.category_entries) + 1
        
        # Category label with fixed width
        ttk.Label(self.scrollable_frame, text=category, width=20).grid(
            row=row, column=0, padx=5, pady=2, sticky="w"
        )
        
        # Goal entry with fixed width
        goal_entry = ttk.Entry(self.scrollable_frame, width=15)
        goal_entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        
        # Tags entry with fixed width
        tags_entry = ttk.Entry(self.scrollable_frame, width=30)
        tags_entry.grid(row=row, column=2, padx=5, pady=2, sticky="ew")
        
        # Delete button
        delete_btn = ttk.Button(
            self.scrollable_frame,
            text="🗑",
            width=3,
            command=lambda c=category: self._confirm_delete_category(c)
        )
        delete_btn.grid(row=row, column=3, padx=5, pady=2)
        
        # Set values if provided
        if goal is not None:
            goal_entry.insert(0, f"{goal:.2f}")
        if tags:
            tags_entry.insert(0, tags)
        
        self.category_entries[category] = (goal_entry, tags_entry)
    
    def _confirm_delete_category(self, category: str) -> None:
        """Show confirmation dialog before deleting a category."""
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the category '{category}'?\n\n"
            "Note: This will not delete transactions in this category."
        ):
            self.db.delete_category(category)
            self._refresh_categories()
    
    def _sort_categories(self, categories: List[tuple]) -> List[tuple]:
        """Sort categories based on current sort settings."""
        reverse = self.sort_direction_var.get() == "desc"
        sort_by = self.sort_var.get()
        
        if sort_by == "name":
            return sorted(categories, key=lambda x: x[0].lower(), reverse=reverse)
        elif sort_by == "goal":
            return sorted(categories, key=lambda x: x[1] if x[1] is not None else Decimal('0'), reverse=reverse)
        else:  # tags
            return sorted(categories, key=lambda x: (x[2] or "").lower(), reverse=reverse)

    def _refresh_categories(self, *args) -> None:
        """Refresh the category list and their goals."""
        print("Starting _refresh_categories")  # Debug log
        
        # Clear existing entries
        for widget in self.scrollable_frame.grid_slaves():
            if int(widget.grid_info()["row"]) > 0:  # Preserve headers
                widget.destroy()
        self.category_entries.clear()
        
        # Get all categories
        categories = self.db.get_all_categories()
        print(f"Found categories: {categories}")  # Debug log
        
        # Get goals and tags
        goals = self.db.get_budget_goals()
        tags = self.db.get_category_tags()
        print(f"Found goals: {goals}")  # Debug log
        print(f"Found tags: {tags}")  # Debug log
        
        # Create list of tuples for sorting
        category_data = [
            (category, goals.get(category), tags.get(category, ""))
            for category in categories
        ]
        print(f"Category data before sorting: {category_data}")  # Debug log
        
        # Sort categories
        sorted_categories = self._sort_categories(category_data)
        print(f"Sorted categories: {sorted_categories}")  # Debug log
        
        # Add rows for each category
        for category, goal, tag in sorted_categories:
            self._add_category_row(category, goal, tag)
        
        self._update_totals()
    
    def _save_all_goals(self) -> None:
        """Save all category goals and tags."""
        print("\n=== Saving Budget Goals ===")
        success_count = 0
        error_count = 0
        
        for category, (goal_entry, tags_entry) in self.category_entries.items():
            goal_value = goal_entry.get().strip()
            tags_value = tags_entry.get().strip()
            
            try:
                # Save goal if provided
                if goal_value:
                    amount = Decimal(goal_value)
                    if amount <= 0:
                        raise ValueError("Amount must be positive")
                    self.db.set_budget_goal(category, amount)
                
                # Always save tags (even if empty)
                if tags_value:  # Only save if tags are not empty
                    self.db.set_category_tags(category, tags_value)
                    print(f"Saved tags for {category}: {tags_value}")
                
                success_count += 1
                
            except (InvalidOperation, ValueError) as e:
                error_count += 1
                messagebox.showerror(
                    "Error",
                    f"Invalid amount for category '{category}': {str(e)}"
                )
        
        print("\n=== After Saving ===")
        self.db.debug_print_categories()
        
        if success_count > 0:
            self._update_totals()
            messagebox.showinfo(
                "Success",
                f"Successfully saved {success_count} budget goals"
                + (f"\n{error_count} errors occurred" if error_count > 0 else "")
            )

    def _verify_database(self) -> None:
        """Verify database connection and content."""
        print("\nDatabase Verification:")
        try:
            transactions = self.db.get_transactions()
            print(f"Total transactions: {len(transactions)}")
            if transactions:
                print(f"Sample categories: {set(t.category for t in transactions[:5])}")
            
            goals = self.db.get_budget_goals()
            print(f"Total budget goals: {len(goals)}")
            print(f"Budget goals: {goals}")
            
        except Exception as e:
            print(f"Database verification failed: {str(e)}") 

    def _update_totals(self) -> None:
        """Update the budget summary totals."""
        # Calculate budget goals
        total_budget_income = Decimal('0')
        total_budget_expense = Decimal('0')
        
        # Get all category tags
        category_tags = self.db.get_category_tags()
        
        for category, (goal_entry, _) in self.category_entries.items():
            try:
                goal_value = goal_entry.get().strip()
                if goal_value:
                    amount = Decimal(goal_value)
                    # Check if category has "income" tag
                    tags = category_tags.get(category, "").lower()
                    if "income" in tags:
                        total_budget_income += amount
                    else:
                        total_budget_expense += amount
            except (InvalidOperation, ValueError):
                continue

        # Get current month's transactions
        current_month = datetime.now().replace(day=1)
        transactions = self.db.get_transactions_for_month(current_month)
        
        # Calculate actual totals
        actual_income = sum(t.amount for t in transactions if t.is_income)
        actual_expenses = sum(t.amount for t in transactions if t.is_expense)
        
        # Calculate balances
        budget_balance = total_budget_income - total_budget_expense
        actual_balance = actual_income - actual_expenses

        # Update budget labels
        self.budget_income_label.config(text=f"Income: ${total_budget_income:,.2f}")
        self.budget_expense_label.config(text=f"Expenses: ${total_budget_expense:,.2f}")
        self.budget_balance_label.config(text=f"Balance: ${budget_balance:,.2f}")

        # Update actual labels
        self.actual_income_label.config(text=f"Income: ${actual_income:,.2f}")
        self.actual_expense_label.config(text=f"Expenses: ${actual_expenses:,.2f}")
        self.actual_balance_label.config(text=f"Balance: ${actual_balance:,.2f}")

    def _setup_sort_controls(self) -> None:
        """Setup the sort controls frame."""
        sort_frame = ttk.Frame(self.parent)
        sort_frame.pack(fill="x", padx=10, pady=5)
        
        # Sort label
        ttk.Label(sort_frame, text="Sort by:").pack(side="left", padx=5)
        
        # Sort options
        self.sort_var = tk.StringVar(value="category")
        sort_options = ttk.OptionMenu(
            sort_frame,
            self.sort_var,
            "category",
            "category",
            "amount",
            command=self._refresh_categories
        )
        sort_options.pack(side="left", padx=5)
        
        # Order options
        self.order_var = tk.StringVar(value="asc")
        ttk.Radiobutton(
            sort_frame,
            text="Ascending",
            variable=self.order_var,
            value="asc",
            command=self._refresh_categories
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            sort_frame,
            text="Descending",
            variable=self.order_var,
            value="desc",
            command=self._refresh_categories
        ).pack(side="left", padx=5) 

    def _on_frame_configure(self, event=None) -> None:
        """Reset the scroll region to encompass the inner frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event=None) -> None:
        """When canvas is resized, resize the inner frame to match."""
        if event:
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width) 