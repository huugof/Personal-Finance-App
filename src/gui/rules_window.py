import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Optional
from database import Database

class RulesWindow:
    """Panel for managing categorization rules."""
    
    def __init__(self, parent: ttk.Frame, db: Database):
        """Initialize the rules panel."""
        self.parent = parent
        self.db = db
        self.is_collapsed = False
        self.EXPANDED_WIDTH = 300  # Constant for expanded width
        
        # Debug logging
        print("\n=== RulesWindow Initialization ===")
        
        # Create the main frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(side="left", fill="y")
        
        # Configure frame width
        self.frame.configure(width=self.EXPANDED_WIDTH)
        self.frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Create header frame
        self.header_frame = ttk.Frame(self.frame)
        self.header_frame.pack(fill="x")
        
        # Create title and button
        self.title_label = ttk.Label(
            self.header_frame,
            text="Rules",
            font=("", 10, "bold")
        )
        self.title_label.pack(side="left", padx=2)
        
        self.collapse_button = ttk.Button(
            self.header_frame,
            text="◀",
            width=2,
            command=self._toggle_collapse
        )
        self.collapse_button.pack(side="right", padx=2)
        
        # Create content frame
        self.content_frame = ttk.Frame(self.frame)
        self.content_frame.pack(fill="both", expand=True)
        
        self._setup_ui()
        self._verify_rules_table()  # Add verification after UI setup
        self._refresh_rules()
        
        print("==============================\n")
    
    def _verify_rules_table(self) -> None:
        """Verify the rules table exists and contains data."""
        try:
            print("\nVerifying rules table...")
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='categorization_rules'
                """)
                if not cursor.fetchone():
                    print("Error: categorization_rules table does not exist!")
                    return
                
                print("✓ categorization_rules table exists")
                
                # Count rules
                cursor.execute("SELECT COUNT(*) FROM categorization_rules")
                count = cursor.fetchone()[0]
                print(f"Found {count} rules in database")
                
                # Show all rules
                cursor.execute("SELECT * FROM categorization_rules")
                rules = cursor.fetchall()
                print("\nExisting rules in database:")
                for rule in rules:
                    print(f"  - {rule}")
                
        except Exception as e:
            print(f"Database verification failed: {str(e)}")
    
    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Update the main_frame setup to use grid instead of pack
        main_frame = ttk.Frame(self.content_frame)
        main_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Add rule section
        add_frame = ttk.LabelFrame(main_frame, text="Add New Rule")
        add_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Pattern field
        ttk.Label(add_frame, text="Pattern:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.pattern_entry = ttk.Entry(add_frame)
        self.pattern_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        # Category field
        ttk.Label(add_frame, text="Category:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.category_entry = ttk.Entry(add_frame)
        self.category_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        # Amount field
        ttk.Label(add_frame, text="Amount (optional):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        amount_frame = ttk.Frame(add_frame)
        amount_frame.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(amount_frame, text="$").pack(side="left")
        self.amount_entry = ttk.Entry(amount_frame, width=15)
        self.amount_entry.pack(side="left", padx=(0, 5))
        
        # Tolerance field
        ttk.Label(add_frame, text="Amount Tolerance (±):").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        tolerance_frame = ttk.Frame(add_frame)
        tolerance_frame.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(tolerance_frame, text="$").pack(side="left")
        self.tolerance_entry = ttk.Entry(tolerance_frame, width=10)
        self.tolerance_entry.pack(side="left", padx=(0, 5))
        self.tolerance_entry.insert(0, "0.01")
        
        # Priority field
        ttk.Label(add_frame, text="Priority:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.priority_entry = ttk.Entry(add_frame, width=8)
        self.priority_entry.grid(row=4, column=1, padx=5, pady=2, sticky="w")
        self.priority_entry.insert(0, "0")
        
        # Add Rule button
        ttk.Button(
            add_frame,
            text="Add Rule",
            command=self._add_rule
        ).grid(row=5, column=0, columnspan=2, pady=5)
        
        # Apply Rules button
        ttk.Button(
            main_frame,
            text="Apply Rules to All Transactions",
            command=self._apply_rules_to_all
        ).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Rules list
        list_frame = ttk.LabelFrame(main_frame, text="Existing Rules")
        list_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # Create Treeview for rules
        self.tree = ttk.Treeview(
            list_frame,
            columns=("Pattern", "Category", "Amount", "Tolerance", "Priority"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.tree.heading("Pattern", text="Pattern")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Amount", text="Amount")
        self.tree.heading("Tolerance", text="±")
        self.tree.heading("Priority", text="Priority")
        
        # Set column widths
        self.tree.column("Pattern", width=150)
        self.tree.column("Category", width=100)
        self.tree.column("Amount", width=80)
        self.tree.column("Tolerance", width=50)
        self.tree.column("Priority", width=50)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Delete button
        ttk.Button(
            main_frame,
            text="Delete Selected Rule",
            command=self._delete_rule
        ).grid(row=3, column=0, columnspan=2, pady=5)

        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # Make rules list expandable
    
    def _add_rule(self) -> None:
        """Add a new categorization rule."""
        try:
            # Get values from inputs
            pattern = self.pattern_entry.get().strip()
            category = self.category_entry.get().strip()
            
            # Validate required fields
            if not pattern or not category:
                messagebox.showerror("Error", "Pattern and category are required")
                return
            
            # Parse amount and tolerance if provided
            amount: Optional[str] = None  # Changed from Decimal to str
            tolerance: Optional[str] = None  # Changed from Decimal to str
            
            if self.amount_entry.get().strip():
                try:
                    # Convert to Decimal for validation, then to string for storage
                    amount = str(Decimal(self.amount_entry.get().strip()))
                except InvalidOperation:
                    messagebox.showerror("Error", "Invalid amount format")
                    return
            
            if self.tolerance_entry.get().strip():
                try:
                    # Convert to Decimal for validation, then to string for storage
                    tolerance = str(Decimal(self.tolerance_entry.get().strip()))
                except InvalidOperation:
                    messagebox.showerror("Error", "Invalid tolerance format")
                    return
            
            # Get priority
            try:
                priority = int(self.priority_entry.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Error", "Priority must be a number")
                return
            
            print(f"\nAdding new rule:")
            print(f"  Pattern: {pattern}")
            print(f"  Category: {category}")
            print(f"  Amount: {amount}")
            print(f"  Tolerance: {tolerance}")
            print(f"  Priority: {priority}")
            
            # Add rule to database with string values for amount and tolerance
            self.db.add_categorization_rule(
                pattern=pattern,
                category=category,
                amount=amount,  # Now a string or None
                tolerance=tolerance,  # Now a string or None
                priority=priority
            )
            
            print("Rule added successfully")
            
            # Refresh display
            self._refresh_rules()
            
            # Clear inputs
            self.pattern_entry.delete(0, tk.END)
            self.category_entry.delete(0, tk.END)
            self.amount_entry.delete(0, tk.END)
            self.tolerance_entry.delete(0, tk.END)
            self.tolerance_entry.insert(0, "0.01")  # Reset to default
            self.priority_entry.delete(0, tk.END)
            self.priority_entry.insert(0, "0")  # Reset to default
            
            # Show success message
            messagebox.showinfo("Success", "Rule added successfully")
            
        except Exception as e:
            print(f"Error adding rule: {str(e)}")
            messagebox.showerror("Error", f"Failed to add rule: {str(e)}")
    
    def _delete_rule(self) -> None:
        """Delete the selected categorization rule."""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = self.tree.item(selection[0])
        pattern = item["values"][0]
        category = item["values"][1]
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this rule?"):
            self.db.delete_categorization_rule(pattern, category)
            self._refresh_rules()
    
    def _apply_rules_to_all(self) -> None:
        """Apply categorization rules to all transactions."""
        if messagebox.askyesno(
            "Confirm Apply Rules",
            "This will apply rules to ALL transactions, potentially overwriting existing categories. Continue?"
        ):
            self.db.apply_rules_to_existing_transactions()
            # Generate an event to notify parent to refresh transactions
            self.parent.event_generate("<<TransactionsChanged>>")
    
    def _refresh_rules(self) -> None:
        """Refresh the rules list."""
        print("\nRefreshing rules display...")
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get and debug print rules
        rules = self.db.get_categorization_rules()
        print(f"Retrieved {len(rules)} rules from database:")
        for rule in rules:
            print(f"  - Pattern: {rule[0]}, Category: {rule[1]}, "
                  f"Amount: {rule[2]}, Tolerance: {rule[3]}, Priority: {rule[4]}")
            
            # Add to treeview
            self.tree.insert("", "end", values=rule)
        
        print("Rules refresh complete")
    
    def _toggle_collapse(self) -> None:
        """Toggle the collapsed state of the rules panel."""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.content_frame.pack_forget()
            self.title_label.pack_forget()
            self.frame.configure(width=40)  # Collapsed width
            self.collapse_button.configure(text="▶")
            self.parent.event_generate("<<RulesPanelCollapsed>>")
        else:
            self.title_label.pack(side="left", padx=2)
            self.content_frame.pack(fill="both", expand=True)
            self.frame.configure(width=self.EXPANDED_WIDTH)  # Expanded width
            self.collapse_button.configure(text="◀")
            self.parent.event_generate("<<RulesPanelExpanded>>") 