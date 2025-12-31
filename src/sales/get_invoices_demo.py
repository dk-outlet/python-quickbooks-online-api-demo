# ===========================================================================
# QuickBooks Online Get Invoices Demo
# Author: Dan Harpold
# License: MIT - Freely use, modify, share. See LICENSE for details.
# Purpose: Demonstrate retrieving invoices from QBO API.
# Last Updated: December 30, 2025
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
    'Content-Type': 'application/text'   # Important: query body is plain text
}

# Full query URL with minorversion
url = f'{API_BASE}{realm_id}/query?minorversion={MINOR_VERSION}'

# query
query = """
SELECT 
    Id, 
    DocNumber, 
    TxnDate, 
    TotalAmt, 
    CustomerRef 
FROM Invoice 
ORDERBY TxnDate DESC
MAXRESULTS 1000
""".strip()

print("Fetching recent invoices from QuickBooks Online...\n")

response = requests.post(
    url,
    headers=headers,
    data=query
)

if response.status_code == 200:
    data = response.json()
    invoices = data.get('QueryResponse', {}).get('Invoice', [])

    if invoices:
        print(f"Found {len(invoices)} recent invoice(s):\n")
        for inv in invoices:
            invoice_id = inv.get('Id', 'N/A')
            doc_number = inv.get('DocNumber', 'N/A')
            date = inv.get('TxnDate', 'N/A')
            total = inv.get('TotalAmt', 0.0)
            customer_ref = inv.get('CustomerRef', {})
            customer_name = customer_ref.get('name', 'Unknown Customer')

            print(f"Invoice ID: {invoice_id}")
            print(f" Doc Number: {doc_number}")
            print(f" Date: {date}")
            print(f" Customer: {customer_name}")
            print(f" Total: ${total:.2f}")
            print("-" * 50)
    else:
        print("No invoices found matching the query.")
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