import os
import time
import json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials


def load_google_credentials():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    if os.path.exists("credentials.json"):
        return Credentials.from_service_account_file("credentials.json", scopes=scope)

    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") or os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if service_account_json:
        try:
            data = json.loads(service_account_json)
            return Credentials.from_service_account_info(data, scopes=scope)
        except Exception as e:
            print(f"Warning: invalid JSON in environment variable: {e}")

    try:
        import streamlit as st
        secrets = getattr(st, "secrets", None)
        if secrets:
            possible_keys = [
                "GOOGLE_SERVICE_ACCOUNT_JSON",
                "GOOGLE_CREDENTIALS_JSON",
                "google_service_account_json",
                "google_credentials_json",
                "google_service_account",
                "google_credentials",
            ]
            for k in possible_keys:
                if k in secrets:
                    val = secrets[k]
                    if isinstance(val, dict):
                        return Credentials.from_service_account_info(val, scopes=scope)
                    try:
                        data = json.loads(val)
                        return Credentials.from_service_account_info(data, scopes=scope)
                    except Exception:
                        pass
            for v in (secrets.values() if isinstance(secrets, dict) else []):
                if isinstance(v, dict) and v.get("type") == "service_account":
                    return Credentials.from_service_account_info(v, scopes=scope)
    except Exception:
        pass

    raise FileNotFoundError(
        "No Google service account credentials found for retry. Provide credentials.json, set GOOGLE_SERVICE_ACCOUNT_JSON, or add the key to Streamlit secrets."
    )


if __name__ == '__main__':
    pending = "pending_tracker_update.csv"
    if not os.path.exists(pending):
        print(f"No pending file found: {pending}")
        raise SystemExit(1)

    try:
        df = pd.read_csv(pending)
    except Exception as e:
        print(f"Failed to read pending file: {e}")
        raise

    header = df.columns.tolist()
    rows = df.values.tolist()
    values = [header] + [[str(v) if pd.notna(v) else "" for v in row] for row in rows]

    try:
        creds = load_google_credentials()
        client = gspread.authorize(creds)
        sheet = client.open("Task Tracker").sheet1

        sheet.clear()
        print("Google Sheets: cleared existing sheet contents")

        max_retries = 5
        backoff = 1
        for attempt in range(1, max_retries + 1):
            try:
                sheet.update('A1', values)
                print(f"Google Sheets: appended {len(rows)} data rows (batch update)")
                print("Google Sheets: update completed successfully")
                # Remove pending file on success
                try:
                    os.remove(pending)
                    print(f"Removed pending file: {pending}")
                except Exception:
                    pass
                raise SystemExit(0)
            except Exception as ex:
                print(f"Google Sheets: update attempt {attempt} failed: {ex}")
                if attempt == max_retries:
                    print("Google Sheets: max retries reached, leaving pending file for manual retry")
                    raise
                sleep_time = backoff + (0.1 * attempt)
                print(f"Google Sheets: retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
                backoff *= 2

    except Exception as e:
        print(f"Retry upload failed: {e}")
        raise
