import tkinter as tk
from tkinter import ttk, messagebox
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
        self._refresh_rules()
    
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
        
        ttk.Label(add_frame, text="Pattern:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.pattern_entry = ttk.Entry(add_frame)
        self.pattern_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(add_frame, text="Category:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.category_entry = ttk.Entry(add_frame)
        self.category_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(add_frame, text="Priority:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.priority_entry = ttk.Entry(add_frame, width=8)
        self.priority_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        self.priority_entry.insert(0, "0")
        
        ttk.Button(
            add_frame,
            text="Add Rule",
            command=self._add_rule
        ).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Add Apply Rules button
        ttk.Button(
            main_frame,
            text="Apply Rules to All Transactions",
            command=self._apply_rules_to_all
        ).grid(row=4, column=0, columnspan=2, pady=5)
        
        # Rules list
        list_frame = ttk.LabelFrame(main_frame, text="Existing Rules")
        list_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Create Treeview for rules with adjusted column widths
        self.tree = ttk.Treeview(
            list_frame,
            columns=("Pattern", "Category", "Priority"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns with specific widths
        self.tree.heading("Pattern", text="Pattern")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Priority", text="Priority")
        
        # Set column widths
        self.tree.column("Pattern", width=100)
        self.tree.column("Category", width=100)
        self.tree.column("Priority", width=50)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack components
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Add delete button
        ttk.Button(
            main_frame,
            text="Delete Selected Rule",
            command=self._delete_rule
        ).grid(row=6, column=0, columnspan=2, pady=5)
    
    def _add_rule(self) -> None:
        """Add a new categorization rule."""
        pattern = self.pattern_entry.get().strip()
        category = self.category_entry.get().strip()
        try:
            priority = int(self.priority_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Priority must be a number")
            return
            
        if not pattern or not category:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        self.db.add_categorization_rule(pattern, category, priority)
        self._refresh_rules()
        
        # Clear inputs
        self.pattern_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.priority_entry.delete(0, tk.END)
        self.priority_entry.insert(0, "0")
    
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
        """Apply categorization rules to all uncategorized transactions."""
        if messagebox.askyesno(
            "Confirm Apply Rules",
            "This will apply rules to all uncategorized transactions. Continue?"
        ):
            updated, total = self.db.apply_rules_to_existing_transactions()
            messagebox.showinfo(
                "Rules Applied",
                f"Updated {updated} out of {total} transactions"
            )
    
    def _refresh_rules(self) -> None:
        """Refresh the rules list."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add current rules
        for pattern, category, priority in self.db.get_categorization_rules():
            self.tree.insert("", "end", values=(pattern, category, priority))
    
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