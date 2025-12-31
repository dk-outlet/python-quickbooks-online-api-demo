# ===========================================================================
# QuickBooks Online Get Sales Receipts Demo
# Author: Dan Harpold
# License: MIT - Freely use, modify, share. See LICENSE for details.
# Purpose: Demonstrate retrieving SalesReceipts from QBO API.
# Last Updated: December 31, 2025
# ===========================================================================

import requests
from auth.auth_demo import get_access_token, get_realm_id

# ----------------------------- CONFIG -----------------------------
# Use sandbox for testing, switch to production when ready
API_BASE = "https://sandbox-quickbooks.api.intuit.com/v3/company/"   # Sandbox
# API_BASE = "https://quickbooks.api.intuit.com/v3/company/"        # Production (uncomment when ready)

# Recommended minorversion as of late 2025
MINOR_VERSION = "73"
# -----------------------------------------------------------------

# Get token and realmId from your auth helper
token = get_access_token()
realm_id = get_realm_id()

# Headers
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json',
    'Content-Type': 'application/text'   # Important for query body
}

# Full query URL with minorversion
url = f'{API_BASE}{realm_id}/query?minorversion={MINOR_VERSION}'

# Query for recent SalesReceipts (fully supported entity)
query = """
SELECT 
    Id, 
    DocNumber, 
    TxnDate, 
    TotalAmt, 
    CustomerRef,
    PaymentRefNum,
    DepositToAccountRef
FROM SalesReceipt 
ORDERBY TxnDate DESC
STARTPOSITION 1
MAXRESULTS 1000
""".strip()

print("Fetching recent Sales Receipts from QuickBooks Online...\n")

response = requests.post(
    url,
    headers=headers,
    data=query
)

if response.status_code == 200:
    data = response.json()
    sales_receipts = data.get('QueryResponse', {}).get('SalesReceipt', [])

    if sales_receipts:
        print(f"Found {len(sales_receipts)} recent Sales Receipt(s):\n")
        for sr in sales_receipts:
            sr_id = sr.get('Id', 'N/A')
            doc_number = sr.get('DocNumber', 'N/A')
            date = sr.get('TxnDate', 'N/A')
            total = sr.get('TotalAmt', 0.0)
            customer_ref = sr.get('CustomerRef', {})
            customer_name = customer_ref.get('name', 'Unknown Customer')
            payment_ref = sr.get('PaymentRefNum', 'N/A')  # e.g., check # or card last 4
            deposit_acct = sr.get('DepositToAccountRef', {}).get('name', 'Undeposited Funds')

            print(f"Sales Receipt ID: {sr_id}")
            print(f" Doc Number: {doc_number}")
            print(f" Date: {date}")
            print(f" Customer: {customer_name}")
            print(f" Total: ${total:.2f}")
            print(f" Payment Ref: {payment_ref}")
            print(f" Deposited To: {deposit_acct}")
            print("-" * 60)
    else:
        print("No Sales Receipts found.")
else:
    print(f"Error {response.status_code}: Request failed")
    try:
        error_data = response.json()
        fault = error_data.get('Fault', {})
        for err in fault.get('Error', []):
            print(f"Code: {err.get('code', 'N/A')}")
            print(f"Message: {err.get('Message', 'N/A')}")
            print(f"Detail: {err.get('Detail', 'N/A')}")
    except ValueError:
        print("Raw response:", response.text)