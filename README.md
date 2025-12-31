# Python QuickBooks Online API Demos

A collection of practical Python demo scripts for integrating with **QuickBooks Online (QBO)** using the official v3 Accounting API.

These examples cover common operations such as:
- Authenticating via OAuth 2.0 (with encrypted refresh token storage)
- Querying Invoices, Sales Receipts, Estimates, and Inventory Items
- Retrieving inventory quantities (SKU + QtyOnHand) with pagination and CSV export
- Creating invoices from existing data (e.g., from Estimates)

Perfect for developers building integrations, internal tools, or learning the QBO API.

## Prerequisites

- Python 3.10 or higher
- A QuickBooks Online developer account: https://developer.intuit.com
- A registered app in the Intuit Developer Portal with the scope `com.intuit.quickbooks.accounting`
- For inventory demos: A **QuickBooks Online Plus** (or Advanced) company with **inventory tracking enabled**

## Repository Structure
```
python-quickbooks-online-api-demo/
├── src/
│   ├── auth/
│   │   └── auth_demo.py          # OAuth 2.0 helper (token management)
│   ├── inventory/
│   │   ├── inventory_items_qty_demo.py     # Export SKU,Qty to CSV (with pagination)
│   │   └── get_inventory_items_demo.py     # List all inventory items
│   ├── invoices/
│   │   └── get_invoices_demo.py            # Query recent invoices
│   ├── salesreceipts/
│   │   └── get_sales_receipts_demo.py      # Query Sales Receipts
│   └── orders/                             # (Estimates used as order alternative)
│       └── get_estimates_demo.py
├── .gitignore
├── LICENSE
└── README.md
```

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/dk-outlet/python-quickbooks-online-api-demo.git
   cd python-quickbooks-online-api-demo

Install dependencies
```Bash
pip install requests cryptography
```

## Configure your Intuit App
- Go to https://developer.intuit.com/app/manager
- Create or edit an app
- Set Redirect URI to: https://localhost:8000/callback
- Note your Client ID and Client Secret
- Update src/auth/auth_demo.py with:
  ```Python
  CLIENT_ID = "YOUR_CLIENT_ID"
  CLIENT_SECRET = "YOUR_CLIENT_SECRET"

## One-Time Authentication Process
The first time you run any demo script, it will perform the OAuth 2.0 flow:

1. A browser window will open asking you to log into QuickBooks and approve access.
2. After approving, you will be redirected to https://localhost:8000/callback?...
3. **Copy the full redirect URL** from your browser address bar.
4. **Paste it** when prompted in the terminal:
   ```text
   After Connect screen, paste the full redirect URL:
5. The script will exchange the code for tokens and save an encrypted refresh token to qbo_tokens.json.
6. Future runs will be completely automatic (no browser or pasting needed).

**Important:** Never commit `qbo_tokens.json` or `encrypt.key` to Git (they are already in .gitignore).
To reconnect to a different company (e.g., new sandbox), delete `qbo_tokens.json` and re-run any script.

Running the Scripts
All scripts are designed to be run as Python modules from the **project root**.

**Example: Get Inventory Quantities (CSV Export)**
```Bash
python -m src.inventory.inventory_items_qty_demo
```
**Example: List Recent Sales Receipts**
```Bash
python -m src.salesreceipts.get_sales_receipts_demo
```
**Example: List All Inventory Items**
```Bash
python -m src.inventory.get_inventory_items_demo
```
**General Pattern**
```Bash
python -m src.<folder>.<script_name_without_py>
```
This ensures proper package imports (e.g., `from auth.auth_demo import ...`).

**Notes**

- Use the sandbox environment for testing (default in most scripts).
- Switch to production by changing `API_BASE` to `https://quickbooks.api.intuit.com/v3/company/` in individual scripts.
- Inventory features require **QBO Plus** with **Track inventory quantity on hand** enabled in company settings.
- Sales Orders are **not supported** via the QBO API (even in Plus) — use Estimates as a common workaround.

**License**
This project is licensed under the MIT License - see the LICENSE file for details.
Happy integrating! 🚀
