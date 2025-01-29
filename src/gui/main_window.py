import tkinter as tk

from tkinter import ttk, messagebox, filedialog
from typing import Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from models.transaction import Transaction
from database import Database
from services.csv_handler import CSVHandler
from gui.budget_goals_window import BudgetGoalsWindow

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
        
        # Initialize UI components
        self._setup_main_tab()
        self._setup_budget_goals_tab()
    
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
        
        # Transactions Table
        self.tree = ttk.Treeview(
            self.main_tab,
            columns=("ID", "Date", "Amount", "Description", "Category", "Type", "Actions"),
            show="headings",
            selectmode="browse"
        )
        
        # Hide ID column but keep it for reference
        self.tree.column("ID", width=0, stretch=False)
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
        for col in self.tree["columns"][1:]:
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
        
        # Initial refresh
        self._refresh_transactions()
    
    def _setup_budget_goals_tab(self) -> None:
        """Set up the budget goals tab UI."""
        BudgetGoalsWindow(self.budget_goals_tab, self.db)
    
    def _add_transaction(self) -> None:
        """Add a new transaction from the input fields."""
        try:
            amount = Decimal(self.amount_entry.get())
            description = self.desc_entry.get().strip()
            category = self.category_entry.get().strip()
            
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
        """Handle CSV file import."""
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if not file_path:
            return
            
        try:
            csv_handler = CSVHandler()
            transactions = csv_handler.import_transactions(file_path)
            
            # Add all transactions to database
            for transaction in transactions:
                self.db.add_transaction(transaction)
            
            self._refresh_transactions()
            messagebox.showinfo(
                "Success", 
                f"Successfully imported {len(transactions)} transactions"
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to import CSV: {str(e)}"
            )
    
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
                    self._confirm_delete_transaction(values[0])  # Pass the ID
    
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
    
    def _refresh_transactions(self) -> None:
        """Refresh the transactions display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get and display transactions
        for transaction in self.db.get_transactions():
            self.tree.insert(
                "",
                "end",
                values=(
                    transaction.id,  # Hidden ID column
                    transaction.date.strftime("%Y-%m-%d"),
                    f"${transaction.amount:.2f}",
                    transaction.description,
                    transaction.category,
                    transaction.transaction_type,
                    "🗑"  # Delete icon in Actions column
                )
            )
    
    def _clear_inputs(self) -> None:
        """Clear all input fields."""
        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
    
    def run(self) -> None:
        """Start the main event loop."""
        self.root.mainloop() 