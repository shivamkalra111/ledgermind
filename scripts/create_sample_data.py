"""
Create sample Excel/CSV data for testing LedgerMind
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import random

# Paths
BASE_DIR = Path(__file__).parent.parent
SAMPLE_DIR = BASE_DIR / "workspace" / "sample_company"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def create_sales_register():
    """Create sample sales register."""
    
    customers = [
        ("ABC Traders", "27AABCA1234A1ZM", "Maharashtra"),
        ("XYZ Enterprises", "29BBBCX5678B1ZN", "Karnataka"),
        ("PQR Industries", "27CCCPQ9012C1ZO", "Maharashtra"),
        ("LMN Solutions", "33DDDLM3456D1ZP", "Tamil Nadu"),
        ("DEF Services", "27EEEDF7890E1ZQ", "Maharashtra"),
    ]
    
    items = [
        ("Software License", "998314", 18),
        ("IT Consulting", "998313", 18),
        ("Hardware - Laptop", "8471", 18),
        ("Training Services", "999293", 18),
        ("Support Services", "998316", 18),
    ]
    
    data = []
    base_date = datetime(2025, 10, 1)
    
    for i in range(50):
        customer = random.choice(customers)
        item = random.choice(items)
        invoice_date = base_date + timedelta(days=random.randint(0, 90))
        taxable = round(random.uniform(10000, 500000), 2)
        
        # Intra-state (same state as company - Maharashtra 27)
        is_intra_state = customer[2] == "Maharashtra"
        
        if is_intra_state:
            cgst = round(taxable * item[2] / 200, 2)
            sgst = cgst
            igst = 0
        else:
            cgst = 0
            sgst = 0
            igst = round(taxable * item[2] / 100, 2)
        
        total = taxable + cgst + sgst + igst
        
        data.append({
            "Invoice No": f"INV/{invoice_date.strftime('%Y%m')}/{i+1:04d}",
            "Invoice Date": invoice_date.strftime("%Y-%m-%d"),
            "Customer Name": customer[0],
            "Customer GSTIN": customer[1],
            "Place of Supply": customer[2],
            "Item Description": item[0],
            "HSN/SAC Code": item[1],
            "Taxable Value": taxable,
            "CGST Rate": item[2]/2 if is_intra_state else 0,
            "CGST Amount": cgst,
            "SGST Rate": item[2]/2 if is_intra_state else 0,
            "SGST Amount": sgst,
            "IGST Rate": item[2] if not is_intra_state else 0,
            "IGST Amount": igst,
            "Total Invoice Value": total,
        })
    
    df = pd.DataFrame(data)
    filepath = SAMPLE_DIR / "sales_register_2025.xlsx"
    df.to_excel(filepath, index=False)
    print(f"✅ Created: {filepath} ({len(data)} rows)")
    return filepath


def create_purchase_ledger():
    """Create sample purchase ledger with some compliance issues."""
    
    vendors = [
        ("Tech Supplies Pvt Ltd", "27AAACT1234A1ZM", True, "micro"),      # MSME
        ("Office Solutions", "27BBBOS5678B1ZN", True, "small"),           # MSME
        ("Cloud Services Inc", "29CCCCS9012C1ZO", False, None),           # Non-MSME
        ("Hardware Mart", "27DDDNM3456D1ZP", True, "micro"),              # MSME
        ("Cleaning Services", "27EEECS7890E1ZQ", False, None),            # Non-MSME
        ("Soap Traders", "27FFFST1111F1ZR", False, None),                 # Has wrong rate
    ]
    
    items = [
        ("Computer Parts", "8473", 18, 18),      # Correct rate
        ("Office Furniture", "9403", 18, 18),    # Correct rate
        ("Cloud Hosting", "998315", 18, 18),     # Correct rate
        ("Soap (Cleaning)", "3401", 5, 18),      # WRONG! Charged 18%, should be 5%
        ("Stationery", "4820", 18, 18),          # Correct rate
        ("Staff Meals", "9963", 5, 5),           # Blocked credit - Section 17(5)
        ("Employee Travel", "9964", 5, 5),       # Blocked credit - Section 17(5)
    ]
    
    data = []
    base_date = datetime(2025, 10, 1)
    
    for i in range(40):
        vendor = random.choice(vendors)
        item = random.choice(items)
        invoice_date = base_date + timedelta(days=random.randint(0, 90))
        taxable = round(random.uniform(5000, 100000), 2)
        
        # Use the "charged" rate (which may be wrong)
        charged_rate = item[3]
        cgst = round(taxable * charged_rate / 200, 2)
        sgst = cgst
        total = taxable + cgst + sgst
        
        # Payment status - some overdue (43B(h) issue)
        if vendor[2]:  # MSME vendor
            days_old = (datetime.now() - invoice_date).days
            if days_old > 45:
                payment_status = "Overdue"
                payment_date = None
            elif random.random() > 0.3:
                payment_date = invoice_date + timedelta(days=random.randint(10, 40))
                payment_status = "Paid"
            else:
                payment_status = "Pending"
                payment_date = None
        else:
            payment_status = "Paid" if random.random() > 0.2 else "Pending"
            payment_date = invoice_date + timedelta(days=random.randint(15, 60)) if payment_status == "Paid" else None
        
        data.append({
            "Bill No": f"BILL/{i+1:04d}",
            "Bill Date": invoice_date.strftime("%Y-%m-%d"),
            "Vendor Name": vendor[0],
            "Vendor GSTIN": vendor[1],
            "Is MSME": "Yes" if vendor[2] else "No",
            "MSME Category": vendor[3] or "",
            "Item Description": item[0],
            "HSN/SAC Code": item[1],
            "Taxable Amount": taxable,
            "CGST %": charged_rate / 2,
            "CGST Amt": cgst,
            "SGST %": charged_rate / 2,
            "SGST Amt": sgst,
            "Total Amount": total,
            "Payment Status": payment_status,
            "Payment Date": payment_date.strftime("%Y-%m-%d") if payment_date else "",
        })
    
    df = pd.DataFrame(data)
    filepath = SAMPLE_DIR / "purchase_ledger_2025.xlsx"
    df.to_excel(filepath, index=False)
    print(f"✅ Created: {filepath} ({len(data)} rows)")
    return filepath


def create_bank_statement():
    """Create sample bank statement."""
    
    data = []
    base_date = datetime(2025, 10, 1)
    balance = 500000.0
    
    transactions = [
        ("Sales Receipt - ABC Traders", "credit", (50000, 200000)),
        ("Sales Receipt - XYZ Enterprises", "credit", (30000, 150000)),
        ("Vendor Payment - Tech Supplies", "debit", (20000, 80000)),
        ("Salary Payment", "debit", (100000, 300000)),
        ("GST Payment", "debit", (10000, 50000)),
        ("Rent Payment", "debit", (25000, 50000)),
        ("Interest Received", "credit", (1000, 5000)),
        ("Utility Payment", "debit", (5000, 15000)),
    ]
    
    for i in range(60):
        txn = random.choice(transactions)
        txn_date = base_date + timedelta(days=i)
        amount = round(random.uniform(*txn[2]), 2)
        
        if txn[1] == "credit":
            balance += amount
            credit = amount
            debit = 0
        else:
            balance -= amount
            credit = 0
            debit = amount
        
        data.append({
            "Date": txn_date.strftime("%Y-%m-%d"),
            "Description": txn[0],
            "Reference": f"TXN{i+1:06d}",
            "Credit": credit if credit > 0 else "",
            "Debit": debit if debit > 0 else "",
            "Balance": round(balance, 2),
        })
    
    df = pd.DataFrame(data)
    filepath = SAMPLE_DIR / "bank_statement_oct_nov_2025.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created: {filepath} ({len(data)} rows)")
    return filepath


def main():
    print("=" * 60)
    print("📊 Creating Sample Data for LedgerMind")
    print("=" * 60)
    print(f"\nOutput directory: {SAMPLE_DIR}\n")
    
    create_sales_register()
    create_purchase_ledger()
    create_bank_statement()
    
    print("\n" + "=" * 60)
    print("✅ Sample data created successfully!")
    print("=" * 60)
    print(f"\nTest with:")
    print(f'  python main.py "analyze folder {SAMPLE_DIR}"')


if __name__ == "__main__":
    main()

