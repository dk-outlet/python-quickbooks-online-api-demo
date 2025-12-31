# ===========================================================================
# QuickBooks Online OAuth Helper
# Author: Dan Harpold
# License: MIT - Freely use, modify, share. See LICENSE for details.
# Purpose: Securely authenticate and refresh tokens for QBO API.
#          Client ID & Secret are prompted once on first run and stored encrypted.
# Last Updated: December 31, 2025
# ===========================================================================

import os
import json
import requests
from urllib.parse import parse_qs, urlparse
from cryptography.fernet import Fernet

# ========================================
# CONFIG - Only static values here
# ========================================
REDIRECT_URI = "https://localhost:8000/callback"  # Must match Intuit app settings
TOKEN_FILE = "qbo_tokens.json"                    # Encrypted storage
KEY_FILE = "encrypt.key"                          # Auto-generated encryption key
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"

class QboAuth:
    def __init__(self):
        self.access_token = None
        self.realm_id = None
        self.client_id = None
        self.client_secret = None
        self._load_or_create_key()

    @property
    def token(self):
        return self.access_token if self.access_token else self.get_access_token()

    def _load_or_create_key(self):
        """Generate or load Fernet encryption key."""
        if not os.path.exists(KEY_FILE):
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as f:
                f.write(key)
        self._fernet = Fernet(open(KEY_FILE, "rb").read())

    def _load_credentials(self):
        """Load encrypted credentials from file."""
        if not os.path.exists(TOKEN_FILE):
            return False
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            encrypted = data["encrypted_data"].encode()
            decrypted = self._fernet.decrypt(encrypted).decode()
            creds = json.loads(decrypted)
            self.client_id = creds["client_id"]
            self.client_secret = creds["client_secret"]
            self.realm_id = creds.get("realm_id")
            encrypted_refresh = data.get("refresh_token")
            if encrypted_refresh:
                self._saved_refresh = self._fernet.decrypt(encrypted_refresh.encode()).decode()
        return True

    def _save_credentials(self, client_id, client_secret, refresh_token, realm_id):
        """Encrypt and save client ID, secret, refresh token, and realm_id."""
        creds = {
            "client_id": client_id,
            "client_secret": client_secret,
            "realm_id": realm_id
        }
        creds_json = json.dumps(creds).encode()
        encrypted_creds = self._fernet.encrypt(creds_json).decode()

        encrypted_refresh = self._fernet.encrypt(refresh_token.encode()).decode()

        with open(TOKEN_FILE, "w") as f:
            json.dump({
                "encrypted_data": encrypted_creds,
                "refresh_token": encrypted_refresh
            }, f)
        print("Credentials and tokens saved securely! Future runs will be automatic.")

    def authenticate_first_time(self):
        """First-time auth: Prompt for Client ID/Secret, open browser, get tokens."""
        print("\n=== First-Time QuickBooks Online Setup ===")
        client_id = input("Enter your Intuit App Client ID: ").strip()
        client_secret = input("Enter your Intuit App Client Secret: ").strip()

        if not client_id or not client_secret:
            raise Exception("Client ID and Secret are required.")

        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "scope": "com.intuit.quickbooks.accounting",
            "state": "secure_state_123",
        }
        auth_url = AUTH_URL + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

        print("\nOpening browser for QuickBooks login...")
        import webbrowser
        webbrowser.open(auth_url)

        callback_url = input("\nAfter approval, paste the full redirect URL here: ").strip()
        code = parse_qs(urlparse(callback_url).query)["code"][0]
        realm_id = parse_qs(urlparse(callback_url).query).get("realmId", [None])[0]

        if not realm_id:
            raise Exception("realmId not found in redirect URL.")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
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
        refresh_token = tokens["refresh_token"]

        self.client_id = client_id
        self.client_secret = client_secret
        self.realm_id = realm_id

        self._save_credentials(client_id, client_secret, refresh_token, realm_id)
        return self.access_token

    def get_access_token(self):
        """Get fresh access token – auto-refresh using saved credentials."""
        if self._load_credentials():
            resp = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._saved_refresh,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code == 200:
                new_tokens = resp.json()
                self.access_token = new_tokens["access_token"]
                new_refresh = new_tokens.get("refresh_token")
                if new_refresh:
                    # Update saved refresh token
                    encrypted_refresh = self._fernet.encrypt(new_refresh.encode()).decode()
                    with open(TOKEN_FILE, "r") as f:
                        data = json.load(f)
                    data["refresh_token"] = encrypted_refresh
                    with open(TOKEN_FILE, "w") as f:
                        json.dump(data, f)
                return self.access_token
        # If load fails or refresh fails → first-time auth
        return self.authenticate_first_time()

# ========================================
# Exported functions for demo scripts
# ========================================
def get_access_token():
    auth = QboAuth()
    return auth.token

def get_realm_id():
    auth = QboAuth()
    if not auth.realm_id:
        # Trigger auth to populate realm_id
        auth.token
    return auth.realm_id