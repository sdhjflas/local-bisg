"""
Generate Google Sheets API token
Run this once to authorize access to Google Sheets
"""

from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes for both Gmail and Sheets
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

print("="*70)
print("Google Sheets Token Generator")
print("="*70)
print("\nA browser window will open. Please:")
print("1. Log in with your Google account")
print("2. Click 'Allow' to grant permissions")
print("3. Return to this terminal\n")

# Use the OAuth credentials file (in parent directory)
flow = InstalledAppFlow.from_client_secrets_file(
    '../client_secret_881609664293-o2k6g5vtm5s0bqjnsig9jri6cs24qmiv.apps.googleusercontent.com.json',
    SCOPES
)

creds = flow.run_local_server(port=8080)

# Save to file
with open('sheets_token.json', 'w') as f:
    f.write(creds.to_json())

print("\n" + "="*70)
print("✅ SUCCESS! Token saved to sheets_token.json")
print("="*70)

# Display token for Railway
with open('sheets_token.json', 'r') as f:
    token_content = f.read().strip()
    # Make it one line
    token_oneline = token_content.replace('\n', '').replace('\r', '')

print("\n📋 COPY THIS FOR RAILWAY GOOGLE_SHEETS_CREDS:")
print("-"*70)
print(token_oneline)
print("-"*70)

print("\n📝 Next Steps:")
print("1. Go to: https://railway.app")
print("2. Open your BISG Labels project")
print("3. Go to Variables")
print("4. Find or create: GOOGLE_SHEETS_CREDS")
print("5. Paste the token above")
print("6. Railway will auto-redeploy")
print("="*70)
