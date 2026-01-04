# Sample Company Data

This folder contains sample Excel/CSV files for testing LedgerMind.

## Expected Files

Place your company's financial files here:

- `sales_register.xlsx` - Sales invoices with GST details
- `purchase_ledger.xlsx` - Purchase bills with vendor details
- `bank_statement.csv` - Bank transactions

## Sample Data Format

### Sales Register
| Invoice No | Date | Customer | GSTIN | Taxable Value | CGST | SGST | Total |
|------------|------|----------|-------|---------------|------|------|-------|
| INV001 | 2025-01-01 | ABC Ltd | 27XXXXX | 10000 | 900 | 900 | 11800 |

### Purchase Ledger
| Bill No | Date | Vendor | GSTIN | Item | Taxable Value | CGST | SGST | Total |
|---------|------|--------|-------|------|---------------|------|------|-------|
| BILL001 | 2025-01-01 | XYZ Traders | 27XXXXX | Soap | 5000 | 450 | 450 | 5900 |

### Bank Statement
| Date | Description | Credit | Debit | Balance |
|------|-------------|--------|-------|---------|
| 2025-01-01 | Sales Receipt | 11800 | | 111800 |

## Usage

```bash
python main.py "analyze folder ./workspace/sample_company/"
```

