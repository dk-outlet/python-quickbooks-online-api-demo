# ===========================================================================
# QuickBooks Online Get Inventory Items Demo
# Author: Dan Harpold
# License: MIT - Freely use, modify, share. See LICENSE for details.
# Purpose: Demonstrate retrieving inventory items from QBO API.
# Last Updated: December 31, 2025
# ===========================================================================

import requests
from auth.auth_demo import get_access_token, get_realm_id

# ----------------------------- CONFIG -----------------------------
# Use sandbox for testing, switch to production when ready
API_BASE = "https://sandbox-quickbooks.api.intuit.com/v3/company/"   # Sandbox
# API_BASE = "https://quickbooks.api.intuit.com/v3/company/"        # Production

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
    'Content-Type': 'application/text'  # Required for query body
}

# Full query URL with minorversion
url = f'{API_BASE}{realm_id}/query?minorversion={MINOR_VERSION}'

# Query to retrieve all ACTIVE inventory items
# SELECT * often returns sparse results — explicitly list key fields to get fuller data
query = """
SELECT 
    Id,
    Name,
    Sku,
    Description,
    UnitPrice,
    QtyOnHand,
    Type,
    Active
FROM Item 
WHERE Type = 'Inventory' AND Active = true
ORDERBY Name ASC
MAXRESULTS 1000
""".strip()

print("Fetching inventory items from QuickBooks Online...\n")

response = requests.post(
    url,
    headers=headers,
    data=query
)

if response.status_code == 200:
    data = response.json()
    items = data.get('QueryResponse', {}).get('Item', [])

    if items:
        print(f"Found {len(items)} inventory item(s):\n")
        print("-" * 80)
        for item in items:
            item_id = item.get('Id', 'N/A')
            name = item.get('Name', 'Unnamed')
            sku = item.get('Sku', 'No SKU')
            qty = item.get('QtyOnHand', 0)
            price = item.get('UnitPrice', 0.0)
            desc = item.get('Description', 'No description')

            print(f"Item ID: {item_id}")
            print(f"  Name:        {name}")
            print(f"  SKU:         {sku}")
            print(f"  Quantity on Hand: {qty}")
            print(f"  Unit Price:  ${price:.2f}")
            print(f"  Description: {desc}")
            print("-" * 80)
    else:
        print("No inventory items found in this company file.")
        print("(Note: Inventory tracking requires QuickBooks Online Plus and must be enabled in company settings.)")
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