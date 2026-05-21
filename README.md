# Task Automation System

This project generates daily tasks from CSV files and optionally updates a Google Sheet named `Task Tracker`.

## Safe Deployment

### Do not commit secrets
Never commit `credentials.json` to GitHub. Add it to `.gitignore` and keep it local.

### Recommended authentication options

#### Option 1: Local development with `credentials.json`
1. Download a Google service account JSON key.
2. Place it in the project root as `credentials.json`.
3. Share the `Task Tracker` Google Sheet with the service account email.

#### Option 2: Cloud deployment with environment variable
Use a secret environment variable instead of a JSON file.

Set the environment variable:
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- or `GOOGLE_CREDENTIALS_JSON`

The value should be the full JSON content of the service account key.

Example in Streamlit Cloud secrets:

```toml
# .streamlit/secrets.toml (local example)
GOOGLE_SERVICE_ACCOUNT_JSON = "{\"type\": \"service_account\", ... }"
```

In Streamlit Cloud, add a secret named `GOOGLE_SERVICE_ACCOUNT_JSON` containing the full JSON text.

### Run the app

```bash
pip install -r requirements.txt
streamlit run app.py
```

## What was changed

- `main.py` now supports both `credentials.json` and the `GOOGLE_SERVICE_ACCOUNT_JSON` environment variable.
- `.gitignore` excludes `credentials.json`, `output.csv`, and Python cache files.

## Notes

- If you share the GitHub repo, do not share `credentials.json`.
- If you deploy the app URL, the deployed app will only update Google Sheets if valid credentials are configured in deployment.
