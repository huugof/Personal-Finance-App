import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Set, Dict, Optional, List
from database import Database
import decimal

class BudgetGoalsWindow:
    """Window for managing category budget goals."""
    
    def __init__(self, parent: ttk.Frame, db: Database) -> None:
        """Initialize the budget goals window."""
        self.parent = parent
        self.db = db
        self.category_entries = {}
        
        # Initialize sort variables
        self.sort_var = tk.StringVar(value="name")
        self.sort_direction_var = tk.StringVar(value="asc")
        
        print("\n=== Opening Budget Goals Window ===")
        self.db.debug_print_categories()
        
        self._verify_database()
        self._setup_ui()
        self._refresh_categories()
    
    def _setup_ui(self) -> None:
        """Set up the budget goals UI."""
        # Add New Category section
        add_frame = ttk.LabelFrame(self.parent, text="Add New Category")
        add_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(add_frame, text="Category Name:").pack(side="left", padx=5)
        self.new_category_entry = ttk.Entry(add_frame)
        self.new_category_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(
            add_frame,
            text="Add Category",
            command=self._add_new_category
        ).pack(side="right", padx=5)
        
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

        # Create main frame for categories
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure grid columns in scrollable frame
        self.scrollable_frame.grid_columnconfigure(1, weight=1, minsize=150)  # Goal column
        self.scrollable_frame.grid_columnconfigure(2, weight=1, minsize=200)  # Tags column
        self.scrollable_frame.grid_columnconfigure(3, minsize=50)  # Delete button column
        
        # Headers with consistent widths
        ttk.Label(self.scrollable_frame, text="Category", font=("", 10, "bold"), width=20).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        ttk.Label(self.scrollable_frame, text="Monthly Goal ($)", font=("", 10, "bold"), width=15).grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        ttk.Label(self.scrollable_frame, text="Tags", font=("", 10, "bold"), width=30).grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        ttk.Label(self.scrollable_frame, text="", width=5).grid(  # Spacer for delete button column
            row=0, column=3, padx=5, pady=5
        )
        
        # Configure canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)  # Connect scrollbar to canvas
        
        # Make the scrollable frame expand to canvas width
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Bind macOS trackpad scrolling
        def _on_scroll(event):
            """Handle scrolling for macOS trackpad."""
            if event.state & 0x1:  # Check if Shift key is held down
                return  # Don't handle horizontal scrolling
            
            # Convert delta to scroll units (-1 or 1)
            if event.delta:
                delta = -1 if event.delta < 0 else 1
                self.canvas.yview_scroll(-delta, "units")
        
        # Bind scroll events
        self.canvas.bind("<MouseWheel>", _on_scroll)
        self.scrollable_frame.bind("<MouseWheel>", _on_scroll)
        
        # Enable scrolling when mouse is over the canvas
        self.canvas.bind('<Enter>', lambda e: self.canvas.bind_all("<MouseWheel>", _on_scroll))
        self.canvas.bind('<Leave>', lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Save Button at bottom
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