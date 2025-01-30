import csv
from datetime import datetime
from decimal import Decimal
from typing import List
from models.transaction import Transaction
import decimal
from database import Database

class CSVHandler:
    """Handles importing transactions from CSV files."""
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """
        Parse date string in various formats.
        Handles formats like:
        - 1/1/2024
        - 01/01/2024
        - 2024-01-01
        - 2024/01/01
        """
        date_formats = [
            "%m/%d/%Y",    # 1/1/2024
            "%m-%d-%Y",    # 1-1-2024
            "%Y-%m-%d",    # 2024-01-01
            "%Y/%m/%d",    # 2024/01/01
            "%d/%m/%Y",    # 01/01/2024
            "%d-%m-%Y",    # 01-01-2024
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue
                
        raise ValueError(f"Unable to parse date: {date_str}")
    
    @staticmethod
    def _parse_amount(amount_str: str) -> Decimal:
        """
        Parse amount string to Decimal, handling common currency formats.
        
        Args:
            amount_str: String representation of amount (e.g., "50.25", "$50.25", "1,234.56")
            
        Returns:
            Decimal: Parsed amount
            
        Raises:
            ValueError: If amount cannot be parsed
        """
        # Remove currency symbols, spaces, and commas
        cleaned_amount = amount_str.strip().replace("$", "").replace(",", "")
        try:
            return Decimal(cleaned_amount)
        except (decimal.InvalidOperation, decimal.ConversionSyntax) as e:
            raise ValueError(f"Invalid amount format: {amount_str}") from e

    @staticmethod
    def import_transactions(file_path: str, db: Database) -> List[Transaction]:
        """
        Import transactions from a CSV file.
        Expected CSV format:
        Date,Amount,Description,Type
        01/02/2025,-382,BRGHTWHL* First...,Daycare
        """
        transactions = []
        
        try:
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                row_count = 0
                error_count = 0
                
                for row_num, row in enumerate(reader, start=2):
                    row_count += 1
                    try:
                        # Print raw row data for debugging
                        print(f"Processing row {row_num}: {row}")
                        
                        amount = CSVHandler._parse_amount(row['Amount'])
                        description = row['Description']
                        
                        # Try to get category from CSV, then from rules if not provided
                        category = row.get('Type', '').strip()
                        if not category:
                            category = db.auto_categorize_transaction(description)
                        
                        if not category:
                            print(f"Warning: No category found for transaction: {description}")
                            category = "Uncategorized"
                        
                        transaction = Transaction(
                            id=None,
                            date=CSVHandler._parse_date(row['Date']),
                            amount=abs(amount),  # Store absolute value
                            description=description,
                            category=category,
                            transaction_type="expense" if amount < 0 else "income"
                        )
                        transactions.append(transaction)
                    except (ValueError, KeyError) as e:
                        error_count += 1
                        print(f"Error processing row {row_num}: {row}. Error: {e}")
                        continue
                
                print(f"\nImport Summary:")
                print(f"Total rows processed: {row_count}")
                print(f"Successful imports: {len(transactions)}")
                print(f"Failed imports: {error_count}")
                
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            return []
                
        return transactions 