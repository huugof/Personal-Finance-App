import tkinter as tk
import sqlite3

from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional, List
from datetime import datetime
from decimal import Decimal, InvalidOperation
from models.transaction import Transaction
from database import Database
from services.csv_handler import CSVHandler
from gui.budget_goals_window import BudgetGoalsWindow
from gui.year_comparison_window import YearComparisonWindow
from gui.graphing_window import GraphingWindow

class MainWindow:
    """Main application window for the budget tracker."""
    
    def __init__(self, db: Database):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Budget Tracker")
        self.db = db
        
        # Initialize variables first
        self.type_var = tk.StringVar(value="expense")
        self.amount_entry = None
        self.desc_entry = None
        self.category_entry = None
        self.tree = None
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        # Create main tab
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Budget Tracker")
        
        # Create budget goals tab
        self.budget_goals_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.budget_goals_tab, text="Budget Goals")
        
        # Create year comparison tab
        self.year_comparison_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.year_comparison_tab, text="Year Comparison")
        
        # Add graphing tab
        self.graphing_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.graphing_tab, text="Graphs")
        GraphingWindow(self.graphing_tab, self.db)
        
        # Create rules tab
        self.rules_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.rules_tab, text="Categorization Rules")
        self._setup_rules_tab()
        
        # Initialize UI components
        self._setup_main_tab()
        self._setup_budget_goals_tab()
        self._setup_year_comparison_tab()
    
    def _setup_main_tab(self) -> None:
        """Set up the main transaction tab UI."""
        # Input Frame
        input_frame = ttk.Frame(self.main_tab)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Amount Entry
        ttk.Label(input_frame, text="Amount:").grid(row=0, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(input_frame)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Description Entry
        ttk.Label(input_frame, text="Description:").grid(row=0, column=2, padx=5, pady=5)
        self.desc_entry = ttk.Entry(input_frame)
        self.desc_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Category Entry
        ttk.Label(input_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5)
        self.category_entry = ttk.Entry(input_frame)
        self.category_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Transaction Type Radio Buttons
        type_frame = ttk.Frame(input_frame)
        type_frame.grid(row=1, column=2, columnspan=2, pady=5)
        
        ttk.Radiobutton(
            type_frame, 
            text="Expense",
            variable=self.type_var,
            value="expense"
        ).pack(side="left", padx=5)
        
        ttk.Radiobutton(
            type_frame,
            text="Income",
            variable=self.type_var,
            value="income"
        ).pack(side="left", padx=5)
        
        # Add Button
        ttk.Button(
            input_frame,
            text="Add Transaction",
            command=self._add_transaction
        ).grid(row=2, column=0, columnspan=4, pady=10)
        
        # Import Frame
        import_frame = ttk.Frame(self.main_tab)
        import_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(
            import_frame,
            text="Import CSV",
            command=self._import_csv
        ).pack(side="left", padx=5)
        
        # Filter Frame
        filter_frame = ttk.LabelFrame(self.main_tab, text="Search & Filter")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Date Range
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(date_frame, text="Date Range:").pack(side="left", padx=5)
        self.start_date = ttk.Entry(date_frame, width=10)
        self.start_date.pack(side="left", padx=2)
        ttk.Label(date_frame, text="to").pack(side="left", padx=2)
        self.end_date = ttk.Entry(date_frame, width=10)
        self.end_date.pack(side="left", padx=2)
        ttk.Label(date_frame, text="(YYYY-MM-DD)").pack(side="left", padx=5)
        
        # Amount Range
        amount_frame = ttk.Frame(filter_frame)
        amount_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(amount_frame, text="Amount Range: $").pack(side="left", padx=5)
        self.min_amount = ttk.Entry(amount_frame, width=10)
        self.min_amount.pack(side="left", padx=2)
        ttk.Label(amount_frame, text="to $").pack(side="left", padx=2)
        self.max_amount = ttk.Entry(amount_frame, width=10)
        self.max_amount.pack(side="left", padx=2)
        
        # Description Search
        desc_frame = ttk.Frame(filter_frame)
        desc_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(desc_frame, text="Description:").pack(side="left", padx=5)
        self.desc_filter = ttk.Entry(desc_frame)
        self.desc_filter.pack(side="left", fill="x", expand=True, padx=2)
        
        # Category and Type Filters
        cat_frame = ttk.Frame(filter_frame)
        cat_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(cat_frame, text="Category:").pack(side="left", padx=5)
        self.category_filter = ttk.Combobox(cat_frame, values=["All", ""])
        self.category_filter.set("All")
        self.category_filter.pack(side="left", padx=2)
        
        ttk.Label(cat_frame, text="Type:").pack(side="left", padx=20)
        self.type_filter = ttk.Combobox(
            cat_frame,
            values=["All", "Income", "Expense"],
            state="readonly",
            width=15
        )
        self.type_filter.set("All")
        self.type_filter.pack(side="left", padx=2)
        
        # Filter Buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(
            button_frame,
            text="Apply Filters",
            command=self._apply_filters
        ).pack(side="left", padx=5)
        ttk.Button(
            button_frame,
            text="Clear Filters",
            command=self._clear_filters
        ).pack(side="left", padx=5)
        
        # Bulk Actions Frame
        bulk_frame = ttk.LabelFrame(self.main_tab, text="Bulk Actions")
        bulk_frame.pack(fill="x", padx=10, pady=5)
        
        # Selection info label
        self.selection_label = ttk.Label(bulk_frame, text="0 items selected")
        self.selection_label.pack(side="left", padx=5)
        
        # Category change dropdown
        ttk.Label(bulk_frame, text="Change category to:").pack(side="left", padx=5)
        self.bulk_category = ttk.Combobox(bulk_frame)
        self.bulk_category.pack(side="left", padx=5)
        
        # Get all categories for the dropdown
        categories = self.db.get_all_categories()
        self.bulk_category["values"] = categories
        
        # Bulk action buttons
        ttk.Button(
            bulk_frame,
            text="Apply Category",
            command=self._bulk_update_category
        ).pack(side="left", padx=5)
        
        ttk.Button(
            bulk_frame,
            text="Delete Selected",
            command=self._bulk_delete
        ).pack(side="left", padx=5)
        
        ttk.Button(
            bulk_frame,
            text="Select All Filtered",
            command=self._select_all_filtered
        ).pack(side="right", padx=5)
        
        # Transactions Table
        self.tree = ttk.Treeview(
            self.main_tab,
            columns=("Select", "ID", "Date", "Amount", "Description", "Category", "Type", "Actions"),
            show="headings",
            selectmode="extended"
        )
        
        # Hide Select and ID columns but keep them for reference
        self.tree.column("Select", width=30, stretch=False)
        self.tree.column("ID", width=0, stretch=False)
        self.tree.heading("Select", text="✓")
        self.tree.heading("ID", text="ID")
        
        # Set column headings and widths
        column_widths = {
            "Date": 100,
            "Amount": 100,
            "Description": 200,
            "Category": 150,
            "Type": 100,
            "Actions": 70
        }
        
        # Configure columns (skipping hidden ID column)
        for col in self.tree["columns"][2:]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 150))
        
        # Configure Actions column
        self.tree.column("Actions", anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.main_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        # Bind click event for delete button
        self.tree.bind("<Button-1>", self._handle_click)
        
        # Bind selection changes
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._update_selection_label())
        
        # Initial refresh
        self._refresh_transactions()
    
    def _setup_budget_goals_tab(self) -> None:
        """Set up the budget goals tab UI."""
        BudgetGoalsWindow(self.budget_goals_tab, self.db)
    
    def _setup_year_comparison_tab(self) -> None:
        """Set up the year comparison tab UI."""
        YearComparisonWindow(self.year_comparison_tab, self.db)
    
    def _setup_rules_tab(self) -> None:
        """Set up the categorization rules tab UI."""
        # Input frame
        input_frame = ttk.LabelFrame(self.rules_tab, text="Add New Rule")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Pattern entry
        ttk.Label(input_frame, text="Pattern:").grid(row=0, column=0, padx=5, pady=5)
        self.pattern_entry = ttk.Entry(input_frame, width=30)
        self.pattern_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Category selection
        ttk.Label(input_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
        categories = sorted(list(self.db.get_all_categories()))
        self.rule_category = ttk.Combobox(input_frame, values=categories)
        self.rule_category.grid(row=0, column=3, padx=5, pady=5)
        
        # Priority entry
        ttk.Label(input_frame, text="Priority:").grid(row=0, column=4, padx=5, pady=5)
        self.priority_entry = ttk.Entry(input_frame, width=5)
        self.priority_entry.insert(0, "0")
        self.priority_entry.grid(row=0, column=5, padx=5, pady=5)
        
        # Add button
        ttk.Button(
            input_frame,
            text="Add Rule",
            command=self._add_categorization_rule
        ).grid(row=0, column=6, padx=10, pady=5)
        
        # Rules list
        self.rules_tree = ttk.Treeview(
            self.rules_tab,
            columns=("Pattern", "Category", "Priority"),
            show="headings"
        )
        
        # Configure columns
        self.rules_tree.heading("Pattern", text="Pattern")
        self.rules_tree.heading("Category", text="Category")
        self.rules_tree.heading("Priority", text="Priority")
        
        # Add scrollbar
        rules_scrollbar = ttk.Scrollbar(self.rules_tab, orient="vertical", command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=rules_scrollbar.set)
        
        # Pack widgets
        self.rules_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        rules_scrollbar.pack(side="right", fill="y")
        
        # Add delete button
        ttk.Button(
            self.rules_tab,
            text="Delete Selected Rule",
            command=self._delete_categorization_rule
        ).pack(side="bottom", pady=5)
        
        # Add apply rules button
        ttk.Button(
            self.rules_tab,
            text="Apply Rules to Existing Transactions",
            command=self._apply_rules_to_existing
        ).pack(side="bottom", pady=5)
        
        # Initial refresh
        self._refresh_rules()
    
    def _add_transaction(self) -> None:
        """Add a new transaction from the input fields."""
        try:
            amount = Decimal(self.amount_entry.get())
            description = self.desc_entry.get().strip()
            category = self.category_entry.get().strip()
            
            # If no category provided, try auto-categorization
            if not category:
                auto_category = self.db.auto_categorize_transaction(description)
                if auto_category:
                    category = auto_category
            
            if not description or not category:
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            transaction = Transaction(
                id=None,
                date=datetime.now(),
                amount=amount,
                description=description,
                category=category,
                transaction_type=self.type_var.get()
            )
            
            self.db.add_transaction(transaction)
            self._refresh_transactions()
            self._clear_inputs()
            
        except InvalidOperation:
            messagebox.showerror("Error", "Please enter a valid amount")
    
    def _import_csv(self) -> None:
        """Import transactions from a CSV file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            transactions = CSVHandler.import_transactions(file_path, self.db)
            for transaction in transactions:
                self.db.add_transaction(transaction)
            self._refresh_transactions()
    
    def _show_context_menu(self, event) -> None:
        """Show context menu on right-click."""
        # Get the item under cursor
        item = self.tree.identify_row(event.y)
        print(f"Right-clicked on item: {item}")  # Debug log
        
        if item:
            # Select the item that was right-clicked
            self.tree.selection_set(item)
            # Show the context menu
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def _handle_click(self, event) -> None:
        """Handle click events on the tree view."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            
            # If it's the Actions column (last column)
            if column == f"#{len(self.tree['columns'])}":
                values = self.tree.item(item)["values"]
                if values:
                    self._confirm_delete_transaction(values[1])  # Pass the ID
    
    def _confirm_delete_transaction(self, transaction_id: int) -> None:
        """Show confirmation dialog before deleting a transaction."""
        if messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this transaction?"
        ):
            try:
                self.db.delete_transaction(transaction_id)
                self._refresh_transactions()
                messagebox.showinfo("Success", "Transaction deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete transaction: {str(e)}")
    
    def _refresh_transactions(self, transactions: Optional[List[Transaction]] = None) -> None:
        """Refresh the transactions display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get transactions if not provided
        if transactions is None:
            transactions = self.db.get_transactions()
        
        # Update category filter options
        categories = ["All"] + sorted(list({t.category for t in transactions}))
        self.category_filter["values"] = categories
        if not self.category_filter.get():
            self.category_filter.set("All")
        
        # Display transactions
        for transaction in transactions:
            self.tree.insert(
                "",
                "end",
                values=(
                    "☐",  # Checkbox column
                    transaction.id,
                    transaction.date.strftime("%Y-%m-%d"),
                    f"${transaction.amount:.2f}",
                    transaction.description,
                    transaction.category,
                    transaction.transaction_type,
                    "🗑"
                )
            )
    
    def _clear_inputs(self) -> None:
        """Clear all input fields."""
        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
    
    def _apply_filters(self) -> None:
        """Apply all filters to the transactions view."""
        try:
            transactions = self.db.get_transactions()
            filtered_transactions = []
            
            # Get filter values
            start_date = None
            end_date = None
            if self.start_date.get().strip():
                start_date = datetime.strptime(self.start_date.get().strip(), "%Y-%m-%d")
            if self.end_date.get().strip():
                end_date = datetime.strptime(self.end_date.get().strip(), "%Y-%m-%d")
            
            # Parse amount filters
            min_amount = None
            max_amount = None
            if self.min_amount.get().strip():
                min_amount = Decimal(self.min_amount.get().strip())
            if self.max_amount.get().strip():
                max_amount = Decimal(self.max_amount.get().strip())
            
            # Get other filter values
            desc_filter = self.desc_filter.get().strip().lower()
            category_filter = self.category_filter.get()
            type_filter = self.type_filter.get()
            
            # Apply filters
            for transaction in transactions:
                # Date filter
                if start_date and transaction.date < start_date:
                    continue
                if end_date and transaction.date > end_date:
                    continue
                
                # Amount filter
                if min_amount is not None and transaction.amount < min_amount:
                    continue
                if max_amount is not None and transaction.amount > max_amount:
                    continue
                
                # Description filter
                if desc_filter and desc_filter not in transaction.description.lower():
                    continue
                
                # Category filter
                if category_filter != "All":
                    if category_filter == "":  # Empty category filter
                        if transaction.category and transaction.category.strip() != "" and transaction.category != "Uncategorized":
                            continue
                    elif transaction.category != category_filter:
                        continue
                
                # Type filter
                if type_filter != "All" and transaction.transaction_type.lower() != type_filter.lower():
                    continue
                
                filtered_transactions.append(transaction)
            
            # Update the tree with filtered transactions
            self._refresh_transactions(filtered_transactions)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid filter value: {str(e)}")
    
    def _clear_filters(self) -> None:
        """Clear all filters and reset the view."""
        self.start_date.delete(0, tk.END)
        self.end_date.delete(0, tk.END)
        self.min_amount.delete(0, tk.END)
        self.max_amount.delete(0, tk.END)
        self.desc_filter.delete(0, tk.END)
        self.category_filter.set("")
        self.type_filter.set("All")
        self._refresh_transactions()
    
    def _update_selection_label(self) -> None:
        """Update the selection count label."""
        selected = len(self.tree.selection())
        self.selection_label.config(text=f"{selected} items selected")
    
    def _bulk_update_category(self) -> None:
        """Bulk update categories for selected transactions."""
        # Get selected items
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "No Selection",
                "Please select one or more transactions to update."
            )
            return

        # Get the new category from the combobox
        new_category = self.bulk_category.get().strip()
        if not new_category:
            messagebox.showwarning(
                "Invalid Category",
                "Please select or enter a valid category."
            )
            return

        try:
            # Update each selected transaction
            for item_id in selected_items:
                transaction_id = self.tree.item(item_id)["values"][1]  # ID is second column
                self.db.update_transaction_category(transaction_id, new_category)
            
            # Refresh the display
            self._refresh_transactions()
            messagebox.showinfo(
                "Success",
                f"Updated {len(selected_items)} transaction(s) to category: {new_category}"
            )
            
            # Update the categories list in the combobox
            categories = self.db.get_all_categories()
            self.bulk_category["values"] = categories
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to update categories: {str(e)}"
            )
    
    def _bulk_delete(self) -> None:
        """Delete multiple selected transactions after confirmation."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "No Selection",
                "Please select one or more transactions to delete."
            )
            return

        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_items)} transaction(s)?"
        ):
            try:
                # Delete each selected transaction
                for item_id in selected_items:
                    transaction_id = self.tree.item(item_id)["values"][1]  # ID is second column
                    self.db.delete_transaction(transaction_id)
                
                # Refresh the display
                self._refresh_transactions()
                messagebox.showinfo(
                    "Success",
                    f"Successfully deleted {len(selected_items)} transaction(s)"
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to delete transactions: {str(e)}"
                )
    
    def _select_all_filtered(self) -> None:
        """Select all transactions currently visible in the tree."""
        # Clear current selection
        self.tree.selection_set()  # Clear selection
        
        # Select all items in the tree
        for item in self.tree.get_children():
            self.tree.selection_add(item)
        
        # Update selection label
        self._update_selection_label()

    def _delete_transaction(self, item: str) -> None:
        """Delete a transaction after confirmation."""
        values = self.tree.item(item)["values"]
        if values:
            transaction_id = values[1]  # ID is second column
            if messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete this transaction?"
            ):
                try:
                    self.db.delete_transaction(transaction_id)
                    self._refresh_transactions()
                except Exception as e:
                    messagebox.showerror(
                        "Error",
                        f"Failed to delete transaction: {str(e)}"
                    )
    
    def _add_categorization_rule(self) -> None:
        """Add a new categorization rule."""
        pattern = self.pattern_entry.get().strip()
        category = self.rule_category.get().strip()
        priority = int(self.priority_entry.get().strip() or "0")
        
        if not pattern or not category:
            messagebox.showerror("Error", "Please fill in both pattern and category")
            return
        
        try:
            self.db.add_categorization_rule(pattern, category, priority)
            self._refresh_rules()
            self.pattern_entry.delete(0, tk.END)
            self.rule_category.set("")
            self.priority_entry.delete(0, tk.END)
            self.priority_entry.insert(0, "0")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add rule: {str(e)}")

    def _delete_categorization_rule(self) -> None:
        """Delete selected categorization rule."""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a rule to delete")
            return
        
        try:
            for item in selected:
                values = self.rules_tree.item(item)["values"]
                self.db.delete_categorization_rule(values[0], values[1])
            self._refresh_rules()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete rule: {str(e)}")

    def _refresh_rules(self) -> None:
        """Refresh the rules display."""
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        rules = self.db.get_categorization_rules()
        for pattern, category, priority in rules:
            self.rules_tree.insert("", "end", values=(pattern, category, priority))
    
    def _apply_rules_to_existing(self) -> None:
        """Apply categorization rules to all existing transactions."""
        if messagebox.askyesno(
            "Confirm Apply Rules",
            "This will apply categorization rules to all uncategorized transactions "
            "and transactions marked as 'Uncategorized'. Continue?"
        ):
            try:
                updated, total = self.db.apply_rules_to_existing_transactions()
                messagebox.showinfo(
                    "Rules Applied",
                    f"Updated {updated} out of {total} transactions."
                )
                self._refresh_transactions()
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to apply rules: {str(e)}"
                )
    
    def run(self) -> None:
        """Start the main event loop."""
        self.root.mainloop() 