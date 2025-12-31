# ===========================================================================
# QuickBooks Online Get Inventory Items Quantity Export Demo
# Author: Dan Harpold
# License: MIT - Freely use, modify, share. See LICENSE for details.
# Purpose: Demonstrate retrieving inventory item quantities from QBO API. Creates a CSV file with SKU,Qty for all ACTIVE items with SKUs
# Last Updated: December 31, 2025
# ===========================================================================

import requests
import csv
from auth.auth_demo import get_access_token, get_realm_id

# ----------------------------- CONFIG -----------------------------
# Use sandbox for testing (switch to production when ready)
API_BASE = "https://sandbox-quickbooks.api.intuit.com/v3/company/"   # Sandbox
# API_BASE = "https://quickbooks.api.intuit.com/v3/company/"        # Production

# Recommended minorversion
MINOR_VERSION = "73"

# Output CSV file
CSV_FILENAME = 'qbo_inventory_qty.csv'

# Maximum results per page (QuickBooks allows up to 1000)
MAX_RESULTS = 1000
# -----------------------------------------------------------------

def fetch_all_inventory_with_sku():
    """Fetch all active inventory items with a SKU, handling pagination."""
    token = get_access_token()
    realm_id = get_realm_id()

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/text'  # Required for query body
    }

    base_url = f'{API_BASE}{realm_id}'
    query_url = f'{base_url}/query?minorversion={MINOR_VERSION}'

    start_position = 1
    all_items = []

    while True:
        # Fixed query: Proper clause order, server-side filter for SKU != ''
        query = f"""
        SELECT * FROM Item 
        WHERE Type = 'Inventory' AND Active = true
        ORDERBY Name ASC
        STARTPOSITION {start_position}
        MAXRESULTS {MAX_RESULTS}
        """.strip()

        response = requests.post(query_url, headers=headers, data=query)

        if response.status_code != 200:
            print(f"Error fetching page (start position {start_position}): {response.status_code}")
            try:
                error_info = response.json()
                fault = error_info.get('Fault', {})
                for err in fault.get('Error', []):
                    print(f"{err.get('code')}: {err.get('Message')} - {err.get('Detail')}")
            except ValueError:
                print(response.text)
            break

        data = response.json()
        query_response = data.get('QueryResponse', {})
        items = query_response.get('Item', [])

        if not items:
            print("No more items found.")
            break

        print(f"Fetched {len(items)} items (page starting at {start_position})")

        for item in items:
            sku = item.get('Sku', '').strip()
            if not sku:
                print(f"Debug: Item {item.get('Id')} has no SKU (Name: {item.get('Name')})")
                continue
            qty = item.get('QtyOnHand', 0)
            all_items.append((sku, qty))

        if len(items) < MAX_RESULTS:
            break

        start_position += MAX_RESULTS

    return all_items


def save_to_csv(items):
    """Save the list of (SKU, Qty) tuples to a CSV file."""
    with open(CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['SKU', 'QuantityOnHand'])  # Header
        writer.writerows(items)

    print(f"\nSuccess! {len(items)} inventory items saved to '{CSV_FILENAME}'")


def main():
    print("Fetching all inventory items with SKUs from QuickBooks Online (with pagination)...\n")
    items = fetch_all_inventory_with_sku()

    if items:
        save_to_csv(items)
    else:
        print("No inventory items with SKUs found.")


if __name__ == '__main__':
    main()