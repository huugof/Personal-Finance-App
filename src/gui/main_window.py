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
from gui.rules_window import RulesWindow

class MainWindow:
    """Main application window for the budget tracker."""
    
    def __init__(self, db: Database):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Budget Tracker")
        self.root.geometry("1200x600")  # Wider initial size
        self.root.minsize(1200, 600)    # Wider minimum size
        self.db = db
        
        # Create main container with PanedWindow
        self.main_paned = ttk.PanedWindow(self.root, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True)
        
        # Left frame for main content
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=4)
        
        # Right frame for rules with fixed width
        self.right_frame = ttk.Frame(self.main_paned, width=300)
        self.right_frame.pack_propagate(False)  # Prevent frame from resizing
        self.main_paned.add(self.right_frame)  # Remove weight parameter
        
        # Initialize variables
        self.type_var = tk.StringVar(value="expense")
        self.amount_entry = None
        self.desc_entry = None
        self.category_entry = None
        self.tree = None
        
        # Create notebook in left frame
        self.notebook = ttk.Notebook(self.left_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.main_tab = ttk.Frame(self.notebook)
        self.budget_goals_tab = ttk.Frame(self.notebook)
        self.year_comparison_tab = ttk.Frame(self.notebook)
        self.graphing_tab = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.main_tab, text="Budget Tracker")
        self.notebook.add(self.budget_goals_tab, text="Budget Goals")
        self.notebook.add(self.year_comparison_tab, text="Year Comparison")
        self.notebook.add(self.graphing_tab, text="Graphs")
        
        # Initialize UI components
        self._setup_main_tab()
        self._setup_budget_goals_tab()
        self._setup_year_comparison_tab()
        GraphingWindow(self.graphing_tab, self.db)
        
        # Store the original sash position
        self.rules_panel_width = 300  # Default width when expanded
        self.COLLAPSED_WIDTH = 40     # Constant for collapsed width
        
        # Add rules panel to right frame
        self.rules_window = RulesWindow(self.right_frame, self.db)
        
        # Bind collapse/expand events
        self.root.bind("<<RulesPanelCollapsed>>", self._handle_rules_panel_collapse)
        self.root.bind("<<RulesPanelExpanded>>", self._handle_rules_panel_expand)
    
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
        
        # Category change dropdown with manual entry
        ttk.Label(bulk_frame, text="Change category to:").pack(side="left", padx=5)
        self.bulk_category = ttk.Combobox(
            bulk_frame,
            width=30,
            state="normal"  # Allow both selection and manual entry
        )
        self.bulk_category.pack(side="left", padx=5)

        # Get initial categories
        try:
            categories = sorted(self.db.get_all_categories())
            print(f"Debug: Initial categories: {categories}")  # Debug print
            self.bulk_category["values"] = categories
            self.category_filter["values"] = ["All"] + categories
        except Exception as e:
            print(f"Error loading categories: {e}")  # Debug print
            messagebox.showerror(
                "Error",
                f"Failed to load categories: {str(e)}"
            )

        # Apply Category button
        ttk.Button(
            bulk_frame,
            text="Apply Category",
            command=self._apply_category_to_selected
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
        
        # Add bulk actions
        ttk.Button(
            bulk_frame,
            text="Toggle Hidden",
            command=self._toggle_ignored_selected
        ).pack(side="left", padx=5)
        
        # Transactions Table
        self._setup_tree()
        
        # Initial refresh of transactions
        self._refresh_transactions()
    
    def _setup_tree(self) -> None:
        """Set up the transaction treeview."""
        # Create scrollbar
        scrollbar = ttk.Scrollbar(self.main_tab)
        scrollbar.pack(side="right", fill="y")

        # Create treeview
        self.tree = ttk.Treeview(
            self.main_tab,
            columns=("date", "id", "amount", "description", "category", "type", "actions", "ignored"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.heading("date", text="Date", command=lambda: self._sort_by("date"))
        self.tree.heading("id", text="ID")
        self.tree.heading("amount", text="Amount", command=lambda: self._sort_by("amount"))
        self.tree.heading("description", text="Description", command=lambda: self._sort_by("description"))
        self.tree.heading("category", text="Category", command=lambda: self._sort_by("category"))
        self.tree.heading("type", text="Type", command=lambda: self._sort_by("type"))
        self.tree.heading("actions", text="Actions")
        self.tree.heading("ignored", text="Ignored")
        
        # Set column widths and alignments
        self.tree.column("date", width=100, anchor="w")
        self.tree.column("id", width=50, anchor="e")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("description", width=300, anchor="w")
        self.tree.column("category", width=150, anchor="w")
        self.tree.column("type", width=100, anchor="w")
        self.tree.column("actions", width=100, anchor="center")
        self.tree.column("ignored", width=70, anchor="center")
        
        # Pack the tree
        self.tree.pack(fill="both", expand=True)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._update_selection_label())
        
        # Bind click event
        self.tree.bind("<Button-1>", self._handle_click)
    
    def _setup_budget_goals_tab(self) -> None:
        """Set up the budget goals tab UI."""
        BudgetGoalsWindow(self.budget_goals_tab, self.db)
    
    def _setup_year_comparison_tab(self) -> None:
        """Set up the year comparison tab UI."""
        YearComparisonWindow(self.year_comparison_tab, self.db)
    
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
            
            if not item:
                return
            
            values = self.tree.item(item)["values"]
            if not values:
                return
            
            # If it's the Actions column
            if column == "#7":  # Actions column
                cell_width = self.tree.column("#7", "width")
                relative_x = event.x - sum(self.tree.column(f"#{i}", "width") for i in range(1, 7))
                
                if relative_x < (cell_width / 2):  # First icon (eye)
                    self._toggle_ignored_selected()  # Use the bulk toggle method
                else:  # Second icon (trash)
                    self._confirm_delete_transaction(values[1])
    
    def _toggle_ignored_selected(self) -> None:
        """Toggle the ignored status of all selected transactions."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "No Selection",
                "Please select one or more transactions to toggle hidden state."
            )
            return

        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all selected transaction IDs and their current ignored states
                transaction_states = []
                for item_id in selected_items:
                    transaction_id = self.tree.item(item_id)["values"][1]  # ID is second column
                    cursor.execute("SELECT ignored FROM transactions WHERE id = ?", (transaction_id,))
                    current_state = bool(cursor.fetchone()[0])
                    transaction_states.append((transaction_id, current_state))
                
                # Determine the new state (toggle based on majority)
                current_states = [state for _, state in transaction_states]
                new_state = not (sum(current_states) > len(current_states) / 2)
                
                # Show confirmation dialog with appropriate message
                action_word = "hide" if new_state else "unhide"
                if not messagebox.askyesno(
                    "Confirm Toggle Hidden",
                    f"Are you sure you want to {action_word} {len(selected_items)} transaction(s)?\n\n"
                    f"Note: Hidden transactions will be excluded from calculations and reports."
                ):
                    return
                
                # Update all selected transactions
                for transaction_id, _ in transaction_states:
                    cursor.execute(
                        "UPDATE transactions SET ignored = ? WHERE id = ?",
                        (new_state, transaction_id)
                    )
                
                conn.commit()
            
            self._refresh_transactions()
            messagebox.showinfo(
                "Success",
                f"Successfully {'hid' if new_state else 'unhid'} {len(selected_items)} transaction(s)"
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to update hidden status: {str(e)}"
            )
    
    def _confirm_delete_transaction(self, transaction_id: int) -> None:
        """Show confirmation dialog before deleting a transaction."""
        if messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this transaction?"
        ):
            try:
                self.db.delete_transaction(transaction_id)
                self._refresh_transactions()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete transaction: {str(e)}")
    
    def _refresh_transactions(self) -> None:
        """Refresh the transaction list."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get filtered transactions
        transactions = self._get_filtered_transactions()
        
        # Update category lists
        categories = sorted(self.db.get_all_categories())
        
        # Update both category dropdowns
        self.bulk_category["values"] = categories
        self.category_filter["values"] = ["All"] + categories
        
        # Set default values if not already set
        if not self.category_filter.get():
            self.category_filter.set("All")
        if not self.bulk_category.get() and categories:
            self.bulk_category.set(categories[0])

        # Add transactions to tree
        for transaction in transactions:
            # Set eye icon based on ignored status
            eye_icon = "👁" if not transaction.ignored else "🚫"
            
            values = (
                transaction.date.strftime("%Y-%m-%d"),
                transaction.id,
                f"${transaction.amount:,.2f}",
                transaction.description,
                transaction.category,
                transaction.transaction_type,
                f"{eye_icon} 🗑",  # Actions column with both icons
                "Yes" if transaction.ignored else "No"
            )
            self.tree.insert("", "end", values=values)
    
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
            self._refresh_transactions()
            
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
    
    def _apply_category_to_selected(self) -> None:
        """Apply the selected category to all selected transactions."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "No Selection",
                "Please select one or more transactions to update."
            )
            return

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
    
    def _handle_rules_panel_collapse(self, event=None) -> None:
        """Handle rules panel collapse event."""
        self.right_frame.configure(width=self.COLLAPSED_WIDTH)
        self.main_paned.sashpos(0, self.root.winfo_width() - self.COLLAPSED_WIDTH)
    
    def _handle_rules_panel_expand(self, event=None) -> None:
        """Handle rules panel expand event."""
        self.right_frame.configure(width=self.rules_panel_width)
        self.main_paned.sashpos(0, self.root.winfo_width() - self.rules_panel_width)
    
    def _sort_by(self, column: str) -> None:
        """Sort treeview by the specified column.
        
        Args:
            column: The column name to sort by
        """
        # Get all items
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children("")]
        
        # Determine sort order (toggle between ascending and descending)
        if not hasattr(self, "_sort_reverse"):
            self._sort_reverse = {}
        self._sort_reverse[column] = not self._sort_reverse.get(column, False)
        
        # Sort items
        items.sort(reverse=self._sort_reverse[column])
        
        # Special handling for date and amount columns
        if column == "date":
            items = [(datetime.strptime(value, "%Y-%m-%d"), item) for value, item in items]
            items.sort(reverse=self._sort_reverse[column])
            items = [(value.strftime("%Y-%m-%d"), item) for value, item in items]
        elif column == "amount":
            items = [(Decimal(value.replace("$", "").replace(",", "")), item) for value, item in items]
            items.sort(reverse=self._sort_reverse[column])
            items = [(f"${value:,.2f}", item) for value, item in items]
        
        # Move items in the tree
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)
        
        # Update column header
        arrow = "▼" if self._sort_reverse[column] else "▲"
        for col in self.tree["columns"]:
            text = self.tree.heading(col)["text"].replace("▲", "").replace("▼", "").strip()
            self.tree.heading(col, text=text)
        self.tree.heading(column, text=f"{self.tree.heading(column)['text'].split()[0]} {arrow}")
    
    def _get_filtered_transactions(self) -> List[Transaction]:
        """Get transactions based on current filter settings."""
        transactions = self.db.get_transactions()
        
        # If no filters are active, return all transactions
        if (not self.start_date.get().strip() and
            not self.end_date.get().strip() and
            not self.min_amount.get().strip() and
            not self.max_amount.get().strip() and
            not self.desc_filter.get().strip() and
            self.category_filter.get() == "All" and
            self.type_filter.get() == "All"):
            return transactions
        
        # Rest of the filtering logic remains the same
        filtered = []
        for transaction in transactions:
            # Apply all filters...
            if self._transaction_matches_filters(transaction):
                filtered.append(transaction)
        
        return filtered

    def _transaction_matches_filters(self, transaction: Transaction) -> bool:
        """Check if a transaction matches all current filters."""
        # Date filters
        if self.start_date.get().strip():
            try:
                start = datetime.strptime(self.start_date.get().strip(), "%Y-%m-%d")
                if transaction.date < start:
                    return False
            except ValueError:
                pass

        if self.end_date.get().strip():
            try:
                end = datetime.strptime(self.end_date.get().strip(), "%Y-%m-%d")
                if transaction.date > end:
                    return False
            except ValueError:
                pass

        # Amount filters
        if self.min_amount.get().strip():
            try:
                min_val = Decimal(self.min_amount.get().strip())
                if transaction.amount < min_val:
                    return False
            except (ValueError, InvalidOperation):
                pass

        if self.max_amount.get().strip():
            try:
                max_val = Decimal(self.max_amount.get().strip())
                if transaction.amount > max_val:
                    return False
            except (ValueError, InvalidOperation):
                pass

        # Description filter
        desc_filter = self.desc_filter.get().strip().lower()
        if desc_filter and desc_filter not in transaction.description.lower():
            return False

        # Category filter
        category = self.category_filter.get()
        if category != "All" and transaction.category != category:
            return False

        # Type filter
        type_filter = self.type_filter.get()
        if type_filter != "All" and transaction.transaction_type.lower() != type_filter.lower():
            return False

        return True
    
    def run(self) -> None:
        """Start the main event loop."""
        self.root.mainloop() 