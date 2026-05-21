import argparse
import pandas as pd
from datetime import datetime
import os
import re
import calendar
import dateutil.parser
from datetime import timedelta
import gspread
from google.oauth2.service_account import Credentials

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--selected-date", dest="selected_date", type=str)
args, _ = parser.parse_known_args()


# ==============================
# GOOGLE SHEET READ FUNCTION
# ==============================

def get_tracker_data():

    print("Google Sheets: loading tracker data from 'Task Tracker'")
    if not os.path.exists("credentials.json"):
        raise FileNotFoundError("credentials.json not found. Please provide a valid service account key file.")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("Task Tracker").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    print(f"Google Sheets: tracker loaded, rows={len(df)} columns={list(df.columns)}")
    return df


# ==============================
# 1. TODAY INFO
# ==============================
user_input = args.selected_date or os.environ.get("SELECTED_DATE")

if user_input and user_input != "None":
    user_input = str(user_input).strip()
    print("RAW SELECTED DATE =", user_input)
    try:
        today = datetime.strptime(user_input, "%Y-%m-%d")
        print("FINAL TODAY DATE =", today)
    except Exception:
        try:
            today = pd.to_datetime(user_input).to_pydatetime()
            print("FINAL TODAY DATE =", today)
        except Exception as e:
            print(f"Invalid date format '{user_input}'. Using today's date. Error: {e}")
            today = datetime.today()
else:
    print("NO SELECTED DATE PROVIDED, using today's date")
    today = datetime.today()


today_day_name = today.strftime("%A")
today_date = today.day

def get_week_of_month(date):
    first_day = date.replace(day=1)
    dom = date.day
    adjusted_dom = dom + first_day.weekday()
    return int((adjusted_dom - 1) / 7) + 1

week_map = {1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth"}
week_number = get_week_of_month(today)
current_week_label = f"{week_map[week_number]} {today_day_name}".lower()

# ==============================
# 2. MATCH FUNCTION
# ==============================
def check_dependent_task(client_keyword, process_keyword):

    try:
        df_t = get_tracker_data()

        prev_bday = today - timedelta(days=1)

        if today.weekday() == 0:
            prev_bday = today - timedelta(days=3)

        date_str = prev_bday.strftime("%Y-%m-%d")

        df_d = df_t[df_t["Date"].astype(str) == date_str]

        for _, row in df_d.iterrows():

            c = str(row.get("Clients", "")).lower()
            p = str(row.get("Process", "")).lower()

            if client_keyword.lower() in c and process_keyword.lower() in p:
                return True

    except Exception as e:
        print("Dependency check error:", e)

    return False

def is_task_today(value, client="", process=""):
    if pd.isna(value):
        return False

    value = str(value).strip().lower()
    value = value.replace("thrusday", "thursday")

    # Strip confusing explanatory text that contains weekdays to prevent false positives
    confusing_text = [
        "or the first monday for weekends and holidays",
        "if the 25th falls on a monday"
    ]
    for c in confusing_text:
        value = value.replace(c, "")

    # --- NEW IGNORE RULES ---
    ignored_phrases = [
        "not required",
        "no longer needed",
        "stop their ongoing file",
        "two files in a month",
        "waiting for live again",
        "notification through onshore mail",
        "as per email request",
        "after receving email",
        "after receiving email",
        "dmg tool request"
    ]
    for p in ignored_phrases:
        if p in value:
            return False

    # --- NEW HARDCODED OVERRIDES ---
    if "15th of every month, or the prior business day or first business day after the 15th" in value or \
       "15th of every month, or the first business day prior or after the 15th" in value:
        target_date = today.replace(day=15)
        if target_date.weekday() == 5:  # Saturday
            target_date += timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            target_date += timedelta(days=1)
        return today.date() == target_date.date()

    if "20th of each month (or first business day after" in value:
        target_date = today.replace(day=20)
        if target_date.weekday() == 5:  # Saturday
            target_date += timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            target_date += timedelta(days=1)
        return today.date() == target_date.date()

    if "17th of each month (or first business day after holiday)" in value:
        target_date = today.replace(day=17)
        if target_date.weekday() == 5:  # Saturday
            target_date += timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            target_date += timedelta(days=1)
        return today.date() == target_date.date()

    if "18th of each month (or first business day after holiday)" in value:
        target_date = today.replace(day=18)
        if target_date.weekday() == 5:  # Saturday
            target_date += timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            target_date += timedelta(days=1)
        return today.date() == target_date.date()

    if "21st of every month, or the first business day after the 21st" in value or \
       "21st of each month (or first business day after holiday)" in value:
        target_date = today.replace(day=21)
        if target_date.weekday() == 5:  # Saturday
            target_date += timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            target_date += timedelta(days=1)
        return today.date() == target_date.date()

    if "22nd of each month (or first business day after holiday)" in value:
        target_date = today.replace(day=22)
        if target_date.weekday() == 5:  # Saturday
            target_date += timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            target_date += timedelta(days=1)
        return today.date() == target_date.date()

    if "25th of each month (or first business day after" in value:
        target_date = today.replace(day=25)
        if target_date.weekday() == 5:  # Saturday
            target_date += timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            target_date += timedelta(days=1)
        return today.date() == target_date.date()

    if "one day prior to 10th of every month" in value:
        target_date = today.replace(day=9)
        if target_date.weekday() == 5:  # Saturday
            target_date -= timedelta(days=1)
        elif target_date.weekday() == 6:  # Sunday
            target_date -= timedelta(days=2)
        return today.date() == target_date.date()

    if "13th of each month (or first business day after holiday)" in value:
        target_date = today.replace(day=13)
        if target_date.weekday() == 5:  # Saturday
            target_date += timedelta(days=2)
        elif target_date.weekday() == 6:  # Sunday
            target_date += timedelta(days=1)
        return today.date() == target_date.date()


    if "following day after mmc dataload" in value:
        return check_dependent_task("mmc", "data load")

    if "next day after hertz census load" in value:
        return check_dependent_task("hertz", "census load")

    if "tuesday after dataload" in value:
        return True if today_day_name.lower() == "tuesday" else False

    if "every thursday after hcm financial load" in value:
        if today_day_name.lower() == "thursday":
            return check_dependent_task("kaiser", "hcm financial")
        return False

    if "last conagra financial file process" in value:
        # Runs on the last Tuesday of the month, as requested
        if today_day_name.lower() == "tuesday":
            if (today + timedelta(days=7)).month != today.month:
                return True
        return False

    if "1st business day of every new quarter" in value or "first business day of every quarter" in value:
        return (today.month in [1, 4, 7, 10] and today.day == 1)

    if "quarterly-first day of the second month" in value:
        return (today.month in [2, 5, 8, 11] and today.day == 1)

    if "20th of janaury" in value or "20th of january" in value:
        return (today.month == 1 and today.day == 20)

    if "first monday start after first bcom" in value:
        return (today_day_name.lower() == "monday" and today.day <= 7)

    if "wednesday, after 2nd tuesday" in value or "after 2nd tuesday, whenever wednesday comes" in value:
        if today_day_name.lower() != "wednesday":
            return False
        first_day = today.replace(day=1)
        offset = (1 - first_day.weekday() + 7) % 7  # Tuesday is 1
        second_tuesday_date = first_day.day + offset + 7

        if second_tuesday_date < today_date <= second_tuesday_date + 7:
            return True
        return False

    # --- MONTH FILTERS FOR QUARTERLY DATES ---
    if "15th of each quarter" in value:
        if today.month not in [1, 4, 7, 10]: return False

    if "25th of the month before each quarter" in value:
        if today.month not in [3, 6, 9, 12]: return False

    if "14th of the month following the quarter" in value:
        if today.month not in [1, 4, 7, 10]: return False

    # --- NTH BUSINESS DAY LOGIC ---
    match_bday = re.search(r'(first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|\d+(?:st|nd|rd|th)?) (business|working) day', value)
    if match_bday:
        word_str = match_bday.group(1)
        word_to_num = {
            "first": 1, "1st": 1,
            "second": 2, "2nd": 2,
            "third": 3, "3rd": 3,
            "fourth": 4, "4th": 4,
            "fifth": 5, "5th": 5
        }
        if word_str in word_to_num:
            n = word_to_num[word_str]
        else:
            # Extract digits
            digits = re.sub(r'\D', '', word_str)
            if digits:
                n = int(digits)
            else:
                n = 0
                
        if n > 0:
            month_start = f"{today.year}-{today.month:02d}-01"
            last_day = calendar.monthrange(today.year, today.month)[1]
            month_end = f"{today.year}-{today.month:02d}-{last_day}"
            bdays = pd.bdate_range(start=month_start, end=month_end)
    
            if 1 <= n <= len(bdays):
                if today.date() == bdays[n-1].date():
                    return True

    # 1. Handle "no longer needed from <date>"
    match_expired = re.search(r'no longer needed from (\d{1,2}/\d{1,2}/\d{4})', value)
    if match_expired:
        expire_date_str = match_expired.group(1)
        try:
            expire_date = dateutil.parser.parse(expire_date_str)
            if today >= expire_date:
                return False
        except Exception:
            pass

    # 2. Handle exception dates: "please process on <day> on <date> and <date>"
    match_exception = re.search(r'please process on (\w+) on (.*?)\)', value)
    if match_exception:
        target_exception_day = match_exception.group(1).lower()
        dates_str = match_exception.group(2)
        date_parts = [p.strip() for p in dates_str.split('and')]
        for dp in date_parts:
            try:
                # Basic replacements for sloppy abbreviation formats (e.g. "Sept'26")
                clean_dp = dp.replace("'", " 20").replace("sept", "sep")
                exc_date = dateutil.parser.parse(clean_dp)

                # If today IS the exact exception date, forcibly run it
                if today.date() == exc_date.date():
                    return True

                # If today is exactly the day AFTER the exception date (its normal schedule), SKIP IT
                if today.date() == exc_date.date() + timedelta(days=1):
                    return False
            except Exception:
                continue

        # If today is the exception day (e.g. Monday), but it was not one of the explicitly parsed dates, avoid running
        if today_day_name.lower() == target_exception_day:
            return False
            
        # Strip the exception phrase from the value so numbers in it don't trigger daily/monthly rules
        value = value.replace(match_exception.group(0), "")

    # Explicitly exclude if it says "except [today]"
    if f"except {today_day_name.lower()}" in value:
        return False

    # Handle "bi-weekly <day>"
    match_biweekly = re.search(r'bi\s*-?\s*weekly\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', value)
    if match_biweekly:
        target_day = match_biweekly.group(1)
        if today_day_name.lower() != target_day:
            return False

        prev_week_day = today - timedelta(days=7)
        prev_week_str1 = prev_week_day.strftime("%d-%m-%Y")
        prev_week_str2 = f"{prev_week_day.day}-{prev_week_day.month:02d}-{prev_week_day.year}"

        was_done = False
        try:
            if os.path.exists("Bi-Weekly Details.csv"):
                with open("Bi-Weekly Details.csv", "r", encoding="utf-8-sig") as f:
                    for line in f:
                        parts = line.split(',')
                        if len(parts) >= 3:
                            date_val = parts[0].strip()
                            if date_val in [prev_week_str1, prev_week_str2]:
                                c = parts[1].strip().lower()
                                p = parts[2].strip().lower()
                                if client and process:
                                    if client.lower() in c and process.lower() in p:
                                        was_done = True
                                        break
        except Exception:
            pass

        if not was_done:
            tracker_date_str = prev_week_day.strftime("%Y-%m-%d")
            try:
                tracker_df = get_tracker_data()
                for _, row in tracker_df.iterrows():
                    date_val = str(row.get("Date", "")).strip()
                    c = str(row.get("Clients", "")).strip().lower()
                    p = str(row.get("Process", "")).strip().lower()
                    if date_val == tracker_date_str:
                        if client and process:
                            if client.lower() in c and process.lower() in p:
                                was_done = True
                                break
            except Exception:
                pass

        if not was_done:
            tracker_date_str = prev_week_day.strftime("%Y-%m-%d")
            tracker_path = None
            for candidate in ["Tracker.csv", "tracker.csv"]:
                if os.path.exists(candidate):
                    tracker_path = candidate
                    break

            if tracker_path is not None:
                try:
                    tracker_df2 = pd.read_csv(tracker_path, encoding="utf-8-sig")
                    for _, row in tracker_df2.iterrows():
                        date_val = str(row.get("Date", "")).strip()
                        c = str(row.get("Clients", row.get("Client", ""))).strip().lower()
                        p = str(row.get("Process", "")).strip().lower()
                        if date_val == tracker_date_str:
                            if client and process:
                                if client.lower() in c and process.lower() in p:
                                    was_done = True
                                    break
                except Exception:
                    pass

        return not was_done

    # Handle "last [weekday]" (e.g. "last friday of the month")
    match_last = re.search(r'last (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', value)
    if match_last:
        target_weekday = match_last.group(1)
        if today_day_name.lower() == target_weekday:
            next_week = today + timedelta(days=7)
            # If adding a week moves us to a new month, it is indeed the last one!
            if next_week.month != today.month:
                return True
            else:
                return False

    # Handle "last day of the month"
    if "last day" in value:
        # If tomorrow is a new month, today is the last day
        if (today + timedelta(days=1)).month != today.month:
            return True
        else:
            return False

    # Handle "after Nth Weekday" (e.g. "after 2nd tuesday")
    word_to_num = {"first": 1, "1st": 1, "1": 1,
                   "second": 2, "2nd": 2, "2": 2,
                   "third": 3, "3rd": 3, "3": 3,
                   "fourth": 4, "4th": 4, "4": 4}
    match = re.search(r'after (first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4) (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', value)
    if match:
        n = word_to_num[match.group(1)]
        target_weekday = match.group(2)
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        target_weekday_idx = days.index(target_weekday)

        first_day = today.replace(day=1)
        offset = (target_weekday_idx - first_day.weekday() + 7) % 7
        target_date = first_day.day + offset + (n - 1) * 7

        if today_date <= target_date:
            return False
        if today_date > target_date + 7:
            return False

    # Build valid dates mapping functionally to today considering weekend roll-overs
    valid_dates = []

    # If today is a weekend, we strictly do NOT trigger number-based scheduled tasks
    # (they will execute on Monday instead)
    if today.weekday() not in [5, 6]:
        valid_dates.append(today)
        if today.weekday() == 0:  # If today is Monday, catch up on Saturday & Sunday
            valid_dates.append(today - timedelta(days=1))
            valid_dates.append(today - timedelta(days=2))

    for d_date in valid_dates:
        # Handle "one day prior to Nth" logic
        match_prior = re.search(r'(one|1) day prior to (\d+)(?:st|nd|rd|th)?', value)
        if match_prior:
            target_day = int(match_prior.group(2))
            trigger_day = target_day - 1
            if d_date.day == trigger_day:
                return True

        # Match exact numerical variations (e.g., '8', '8th') without catching '18' or '8/'
        # Avoid matching if followed by "business" or "working" (handled separately)
        pattern = r'(?<!/)\b' + str(d_date.day) + r'(st|nd|rd|th)?\b(?!\s*(?:business|working))(?!/)'
        if re.search(pattern, value):
            return True

        # Match explicit m/d or mm/dd formats for the correct mapped date
        md_str = f"{d_date.month}/{d_date.day}"
        mmdd_str = f"{d_date.month:02d}/{d_date.day:02d}"
        if md_str in value or mmdd_str in value:
            return True

    # Match substrings indicating daily frequency
    if "daily" in value:
        return True

    # Match substrings with today's day name (e.g., 'bi-weekly wednesday')
    if today_day_name.lower() in value:
        return True

    # Match week of month patterns if any
    if value == current_week_label:
        return True

    return False

# ==============================
# 3. STANDARDIZE COLUMNS
# ==============================
def standardize_columns(df):
    df.columns = df.columns.str.strip()

    rename_map = {
        "Client": "Clients",
        "Client Name": "Clients",
        "Process Name": "Process"
    }

    df.rename(columns=rename_map, inplace=True)
    return df

# ==============================
# 4. LOAD MAIN FILES
# ==============================
main_files = ["DATALOAD.csv", "REPORT.csv"]

main_dfs = []
for file in main_files:
    if os.path.exists(file):
        df = pd.read_csv(file)
        df = standardize_columns(df)
        df["Source"] = file.upper()
        main_dfs.append(df)

main_df = pd.concat(main_dfs, ignore_index=True)

# ==============================
# 5. CLIENT FILE MAP
# ==============================
all_files = {
    f.lower().strip(): f
    for f in os.listdir()
    if f.lower().endswith(".csv")
}

# ==============================
# 6. PROCESS DATA
# ==============================
final_data = []

for _, row in main_df.iterrows():

    schedule = str(row.get("Scheduled Day", "")).strip().lower()

    # NORMAL CASE
    if schedule not in ["as per calendar", "as per calender", "acc. to processing calender"]:
        client_name = str(row.get("Clients", "")).strip()
        process_name = str(row.get("Process", "")).strip()
        if is_task_today(schedule, client_name, process_name):
            final_data.append(row.to_dict())

    # AS PER CALENDAR
    else:
        original_client_name = str(row.get("Clients", "")).strip()
        client_name = original_client_name.lower()

        if not client_name:
            continue

        if client_name in ["kinder morgan", "el paso"]:
            expected_file = "el paso.csv"
        else:
            expected_file = f"{client_name}.csv"
            
        file_name = all_files.get(expected_file)

        if file_name:
            client_df = pd.read_csv(file_name)
            client_df = standardize_columns(client_df)

            if "Scheduled Day" in client_df.columns:
                def check_cal_row(r):
                    return is_task_today(
                        r["Scheduled Day"],
                        str(r.get("Clients", client_name)).strip(),
                        str(r.get("Process", "")).strip()
                    )
                filtered_client = client_df[client_df.apply(check_cal_row, axis=1)].copy()
            elif "Date" in client_df.columns:
                current_date_str = today.strftime("%Y-%m-%d")
                filtered_client = client_df[
                    client_df["Date"].astype(str) == current_date_str
                ].copy()
            elif "Preliminary File" in client_df.columns:
                current_date_str = today.strftime("%Y-%m-%d")
                filtered_client = client_df[
                    client_df["Preliminary File"].astype(str) == current_date_str
                ].copy()
            else:
                continue

            # 🔥 IMPORTANT: fill client name if missing
            filtered_client["Clients"] = filtered_client.get("Clients", original_client_name)
            filtered_client["Source"] = row.get("Source", "DATALOAD.CSV")

            # Carry over default values from the parent row if missing in the calendar file
            for col in ["Process", "Scheduled Day", "TAT", "Process AHT", "Peer review AHT"]:
                if col not in filtered_client.columns and col in row:
                    filtered_client[col] = row[col]

            final_data.extend(filtered_client.to_dict("records"))

# ==============================
# 7. FINAL OUTPUT
# ==============================
final_df = pd.DataFrame(final_data)

final_df.drop_duplicates(inplace=True)

# Add Date
final_df["Date"] = today.strftime("%Y-%m-%d")

# Required columns
required_columns = [
    "Date",
    "Clients",
    "Process",
    "Scheduled Day",
    "TAT",
    "Process AHT",
    "Peer review AHT"
]

# Ensure columns exist
for col in required_columns:
    if col not in final_df.columns:
        final_df[col] = ""

# Ensure Source column exists just in case
if "Source" not in final_df.columns:
    final_df["Source"] = "DATALOAD.CSV"

# Final selection including Source for separation
final_df = final_df[required_columns + ["Source"]]

# Save
output_file = "output.csv"

# Overwrite the file completely with the new data, separated visually
with open(output_file, 'w') as f:
    df_dataload = final_df[final_df["Source"] == "DATALOAD.CSV"].drop(columns=["Source"])
    f.write("DATALOAD\n")
    df_dataload.to_csv(f, index=False)

    df_report = final_df[final_df["Source"] == "REPORT.CSV"].drop(columns=["Source"])
    if not df_report.empty:
        f.write("\nREPORT\n")
        df_report.to_csv(f, index=False)

print(f"\n✅ File successfully updated (previous data cleared): {output_file}")
print(f"📊 Tasks for {today.strftime('%Y-%m-%d')}: {len(final_df)}")

# ==============================
# 8. SAVE TO GOOGLE SHEET
# ==============================

print("Google Sheets: updating Task Tracker sheet")
try:

    tracker_df = get_tracker_data()

    current_date_str = today.strftime("%Y-%m-%d")

    # Remove existing rows of today's date
    if not tracker_df.empty:
        tracker_df = tracker_df[
            tracker_df["Date"].astype(str) != current_date_str
        ]

    # Combine old + new
    updated_tracker = pd.concat(
        [tracker_df, final_df],
        ignore_index=True
    )

    # Remove duplicates
    updated_tracker.drop_duplicates(inplace=True)

    # Sort by Date
    updated_tracker = updated_tracker.sort_values(
        by="Date",
        ignore_index=True
    )

    # Connect to Google Sheets
    if not os.path.exists("credentials.json"):
        raise FileNotFoundError("credentials.json not found. Please provide a valid service account key file.")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("Task Tracker").sheet1

    sheet.clear()
    print("Google Sheets: cleared existing sheet contents")

    # Add header
    header = updated_tracker.columns.tolist()
    sheet.append_row(header)
    print(f"Google Sheets: appended header {header}")

    # Add data
    rows = updated_tracker.astype(str).values.tolist()
    for index, row in enumerate(rows, start=1):
        sheet.append_row(row)
    print(f"Google Sheets: appended {len(rows)} data rows")
    print("Google Sheets: update completed successfully")

except Exception as e:
    print("Google Sheets: update failed:", e)
    print(f"⚠️ Could not update Google Sheet: {e}")
