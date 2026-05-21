import streamlit as st
from datetime import datetime
import os
import sys
import pandas as pd
import subprocess

st.set_page_config(page_title="Task Automation System", layout="wide")
st.title("Task Automation System")
st.markdown(
    "Generate task output for a selected date and review the results directly in the Streamlit app."
)

selected_date = st.date_input("Select Date", value=datetime.today())

if st.button("Generate Tasks"):

    target_date = selected_date.strftime("%Y-%m-%d")
    st.info(f"Generating tasks for **{target_date}**...")

    result = subprocess.run(
        [sys.executable, "main.py", "--selected-date", target_date],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        st.success(f"Task generation completed for **{target_date}**.")
    else:
        st.error(f"Task generation failed with exit code {result.returncode}.")

    with st.expander("View generation logs"):
        if result.stdout:
            st.subheader("Standard Output")
            st.code(result.stdout.strip(), language="bash")

        if result.stderr:
            st.subheader("Standard Error")
            st.code(result.stderr.strip(), language="bash")

        if not result.stdout and not result.stderr:
            st.write("No log output was produced.")

    if os.path.exists("output.csv"):
        df = pd.read_csv("output.csv")
        st.success("Tasks Generated Successfully ✅")
        st.dataframe(df)
    else:
        st.warning("No output file was generated. Please verify the logs and try again.")