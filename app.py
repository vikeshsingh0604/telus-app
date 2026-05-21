import streamlit as st
from datetime import datetime
import os
import sys
import pandas as pd
import runpy
import io
import contextlib

st.set_page_config(page_title="Task Automation System", layout="wide")
st.title("Task Automation System")
st.markdown(
    "Generate task output for a selected date and review the results directly in the Streamlit app."
)

selected_date = st.date_input("Select Date", value=datetime.today())

if st.button("Generate Tasks"):

    target_date = selected_date.strftime("%Y-%m-%d")
    st.info(f"Generating tasks for **{target_date}**...")

    # Set selected date in environment so main.py can read it
    old_env = os.environ.get("SELECTED_DATE")
    os.environ["SELECTED_DATE"] = target_date

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            # Execute main.py in-process so Streamlit secrets are available
            runpy.run_path("main.py", run_name="__main__")
        st.success(f"Task generation completed for **{target_date}**.")
    except SystemExit as e:
        # main.py may call sys.exit; capture this as failure
        stderr_buf.write(f"SystemExit: {e}\n")
        st.error(f"Task generation exited: {e}")
    except Exception as e:
        stderr_buf.write(str(e) + "\n")
        st.error(f"Task generation failed: {e}")
    finally:
        # restore env
        if old_env is None:
            os.environ.pop("SELECTED_DATE", None)
        else:
            os.environ["SELECTED_DATE"] = old_env

    stdout_val = stdout_buf.getvalue()
    stderr_val = stderr_buf.getvalue()

    with st.expander("View generation logs"):
        if stdout_val:
            st.subheader("Standard Output")
            st.code(stdout_val.strip(), language="bash")

        if stderr_val:
            st.subheader("Standard Error")
            st.code(stderr_val.strip(), language="bash")

        if not stdout_val and not stderr_val:
            st.write("No log output was produced.")

    if os.path.exists("output.csv"):
        df = pd.read_csv("output.csv")
        st.success("Tasks Generated Successfully ✅")
        st.dataframe(df)
    else:
        st.warning("No output file was generated. Please verify the logs and try again.")