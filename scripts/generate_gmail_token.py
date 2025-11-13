"""
Generate Gmail API token for sending emails
Run this script locally to authorize the app and generate token.json
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scope for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    """Generates token.json for Gmail API authentication"""

    # Path to credentials file
    credentials_file = '../client_secret_881609664293-o2k6g5vtm5s0bqjnsig9jri6cs24qmiv.apps.googleusercontent.com.json'

    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        print("Please download OAuth credentials from Google Cloud Console")
        return

    creds = None
    token_file = 'token.json'

    # Check if token already exists
    if os.path.exists(token_file):
        print(f"✅ Token file already exists: {token_file}")
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth flow...")
            print("📧 Make sure to log in with: labels@bisglabels.com")
            print("\nA browser window will open. Please:")
            print("1. Log in with labels@bisglabels.com")
            print("2. Click 'Allow' to grant permissions")
            print("3. Return to this terminal\n")

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save credentials for future use
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

        print(f"\n✅ Token saved to: {token_file}")

    print("\n🎉 Gmail API authentication successful!")
    print(f"\n📋 Next steps:")
    print(f"1. Copy {token_file} to Railway")
    print(f"2. Set GMAIL_TOKEN environment variable in Railway")
    print(f"3. Deploy updated email_sender.py")

if __name__ == '__main__':
    main()
