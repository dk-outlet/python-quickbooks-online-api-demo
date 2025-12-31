
# ===========================================================================
# QuickBooks Online OAuth Helper
# Author: Dan Harpold
# License: MIT - Freely use, modify, share. See LICENSE for details.
# Purpose: Securely authenticate and refresh tokens for QBO API.
# Last Updated: December 27, 2025
# ===========================================================================
# Reusable module: One-time browser OAuth → encrypted refresh token → silent access.
# Perfect for cron jobs, Lambda, or client tools — runs headless after first run.

import os
import json
import requests
from urllib.parse import parse_qs, urlparse
from cryptography.fernet import Fernet

# ========================================
# CONFIG - Set these once per app/environment
# ========================================
CLIENT_ID = "YOUR_CLIENT_ID"  # From Intuit Developer App (Development Keys)
CLIENT_SECRET = "YOUR_CLIENT_SECRET"  # Keep secure 
REDIRECT_URI = "https://localhost:8000/callback"  # Must match in app settings
TOKEN_FILE = "qbo_tokens.json"  # Stores encrypted refresh token
KEY_FILE = "encrypt.key"  # Fernet encryption key (auto-generated)
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
AUTH_URL = "https://appcenter.intuit.com/connect/oauth2?"


class QboAuth:
   def __init__(self):
       self.access_token = None
       self.realm_id = None
       self._load_or_create_key()

   @property 
   def token(self):
       # Read-only access to the current token, refreshes if needed.
       return self.access_token if self.access_token else self.get_access_token()


   def _load_or_create_key(self):
       # Generate or load Fernet encryption key.
       if not os.path.exists(KEY_FILE):
           key = Fernet.generate_key()
           with open(KEY_FILE, "wb") as f:
               f.write(key)
       self._fernet = Fernet(open(KEY_FILE, "rb").read())

   def authenticate_first_time(self):
       # Run once: Opens browser → user clicks 'Connect' → saves refresh token.
       print("Opening browser... please log in and approve access.")
       params = {
           "response_type": "code",
           "client_id": CLIENT_ID,
           "redirect_uri": REDIRECT_URI,
           "scope": "com.intuit.quickbooks.accounting",
           "state": "secure_state_123",
       }

       auth_url = AUTH_URL + "&".join([f"{k}={v}" for k, v in params.items()])

       import webbrowser

       webbrowser.open(auth_url)

       callback_url = input(
           "\nAfter Connect screen, paste the full redirect URL: "
       ).strip()

       parsed = urlparse(callback_url)
       query_params = parse_qs(parsed.query)
       code = query_params["code"][0]
       realm_id = query_params.get("realmId", [None])[0]

       data = {
           "grant_type": "authorization_code",
           "code": code,
           "redirect_uri": REDIRECT_URI,
           "client_id": CLIENT_ID,
           "client_secret": CLIENT_SECRET,
       }

       resp = requests.post(
           TOKEN_URL,
           data=data,
           headers={"Content-Type": "application/x-www-form-urlencoded"},
       )

       if resp.status_code != 200:
           raise Exception(f"Auth failed: {resp.json()}")
              
       tokens = resp.json()
       self.access_token = tokens["access_token"]
       self.realm_id = realm_id # Save it on the instance

       # Save encrypted refresh token
       refresh_token = tokens["refresh_token"]
       encrypted_refresh = self._fernet.encrypt(refresh_token.encode()).decode()
       with open(TOKEN_FILE, "w") as f:
           json.dump({
               "refresh_token": encrypted_refresh,
               "realm_id": realm_id
           }, f)
           print("Token saved! Future runs will be automatic.")

       return self.access_token

   def get_access_token(self):
       # Main method: Get token — auto-refreshes if needed.

       if os.path.exists(TOKEN_FILE):
           with open(TOKEN_FILE, "r") as f:
               data = json.load(f)

               encrypted_refresh = data["refresh_token"]
               self.realm_id = data.get("realm_id")

               refresh_token = self._fernet.decrypt(
                    encrypted_refresh.encode()
               ).decode()

               resp = requests.post(
                   TOKEN_URL,
                   data={
                       "grant_type": "refresh_token",
                       "refresh_token": refresh_token,
                       "client_id": CLIENT_ID,
                       "client_secret": CLIENT_SECRET,
                   },
                   headers={"Content-Type": "application/x-www-form-urlencoded"},
               )

               if resp.status_code == 200:
                   new_tokens = resp.json()
                   self.access_token = new_tokens["access_token"]

                   # Update saved token if refresh is renewed
                   new_refresh = new_tokens.get("refresh_token")
                   if new_refresh:
                       encrypted_refresh = self._fernet.encrypt(
                           new_refresh.encode()
                       ).decode()
                       data["refresh_token"] = encrypted_refresh

                       with open(TOKEN_FILE, "w") as f:
                           json.dump(data, f)
                       return self.access_token
               else:
                   os.remove(TOKEN_FILE)
               # Bad token — start over

       return self.authenticate_first_time()

# ========================================
# Simple functions for other demos to import
# ========================================
# Create a module-level instance so we only ever have one
_auth_instance = QboAuth()

def get_access_token() -> str:
    """
    Returns a valid access token.
    Automatically handles first-time auth and refresh.
    Safe to call from any other script.
    """
    return _auth_instance.get_access_token()

def get_realm_id() -> str:
    """
    QuickBooks requires the realmId (company ID) in every request.
    This pulls it from the discovery endpoint the first time and caches it.
    """
    if not hasattr(_auth_instance, 'realm_id'):
        raise Exception("realmId not available. Re-run initial authentication.")
    return _auth_instance.realm_id        # Use the discovery endpoint to get realmId (works in sandbox & production)


# ========================================
# USAGE EXAMPLE
# ========================================
if __name__ == '__main__':
    auth = QboAuth()
    token = get_access_token()
    realm = get_realm_id()
    print("Access Token:", token[:30] + "...")
    print("Realm ID    :", realm)
    print("\nYou can now use these in other scripts:")
    print("   from auth_demo import get_access_token, get_realm_id")


# Now use token to call QBO APIs like /query, /salesreceipt, etc.
# Example: requests.get('https://quickbooks.api.intuit.com/v3/company/123/query?query=SELECT FROM Customer', headers={'Authorization': f'Bearer {token}'})
