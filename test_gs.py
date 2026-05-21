import os
import json
from google.oauth2.service_account import Credentials
import gspread


def main():
    cwd = os.getcwd()
    cred_path = os.path.join(cwd, "credentials.json")

    if not os.path.exists(cred_path):
        print("credentials.json not found in current directory.")
        print("Place the downloaded service account JSON key as 'credentials.json' here:")
        print(cwd)
        return

    with open(cred_path, "r") as f:
        data = json.load(f)
    sa_email = data.get("client_email")
    if sa_email:
        print("Service account email (share this with your sheet):", sa_email)

    SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(cred_path, scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        sh = client.open("Task Tracker")
        print("Sheet title:", sh.title)
        ws = sh.sheet1
        rows = ws.get_all_values()
        print(f"Rows: {len(rows)}")
        if rows:
            print("First row:", rows[0])
    except Exception as e:
        print("Error accessing sheet:", e)


if __name__ == '__main__':
    main()
