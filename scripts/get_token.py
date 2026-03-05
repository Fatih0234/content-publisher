"""
One-time script to get a LinkedIn OAuth2 access token and your author URN.
Run: python scripts/get_token.py
"""
import http.server
import threading
import urllib.parse
import webbrowser
import requests
import sys

CLIENT_ID     = input("Client ID: ").strip()
CLIENT_SECRET = input("Client Secret: ").strip()
REDIRECT_URI  = "http://localhost:8000/callback"
SCOPES        = "openid profile w_member_social"

auth_url = (
    "https://www.linkedin.com/oauth/v2/authorization"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope={urllib.parse.quote(SCOPES)}"
)

code_holder = {}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            code_holder["code"] = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Got it! You can close this tab.")
        else:
            error = params.get("error", ["unknown"])[0]
            desc  = params.get("error_description", ["no description"])[0]
            code_holder["error"] = f"{error}: {desc}"
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Error: {error} — {desc}".encode())
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args):
        pass

server = http.server.HTTPServer(("localhost", 8000), Handler)
print(f"\nOpening browser for authorization...")
webbrowser.open(auth_url)
print("Waiting for callback (authorize in the browser)...")
server.serve_forever()

code = code_holder.get("code")
if not code:
    err = code_holder.get("error", "no callback received at all")
    print(f"ERROR: {err}")
    sys.exit(1)

# Exchange code for token
resp = requests.post(
    "https://www.linkedin.com/oauth/v2/accessToken",
    data={
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=15,
)
resp.raise_for_status()
token_data = resp.json()
access_token = token_data["access_token"]
expires_in   = token_data.get("expires_in", "unknown")

# Fetch author URN via OpenID userinfo
userinfo = requests.get(
    "https://api.linkedin.com/v2/userinfo",
    headers={"Authorization": f"Bearer {access_token}"},
    timeout=15,
).json()

author_urn = f"urn:li:person:{userinfo['sub']}"
name       = userinfo.get("name", "unknown")

print(f"""
=== Success ===
Name:         {name}
Author URN:   {author_urn}
Access token: {access_token}
Expires in:   {expires_in} seconds (~{int(expires_in)//86400} days)

Run this SQL in Supabase to insert the account:

INSERT INTO linkedin_accounts (label, actor_type, author_urn, access_token)
VALUES (
  'my-account',
  'person',
  '{author_urn}',
  '{access_token}'
);
""")
