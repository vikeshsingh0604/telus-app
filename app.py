import streamlit as st
from datetime import date
import os
import sys
import pandas as pd
import runpy
import io
import contextlib

st.set_page_config(page_title="Telus International Task Automation", page_icon="🌍", layout="wide")

st.markdown(
    "<style>"
    ".block-container { padding-top: 1rem; padding-left: 2rem; padding-right: 2rem; }"
    ".hero-card { background: linear-gradient(135deg, #0078be 0%, #00b4f0 100%); border-radius: 28px; padding: 32px; box-shadow: 0 24px 60px rgba(0, 0, 0, 0.14); color: #ffffff; }"
    ".hero-card h1 { margin-bottom: 8px; font-size: 3rem; }"
    ".hero-card p { margin-top: 0.4rem; font-size: 1.05rem; max-width: 760px; }"
    ".feature-card { background: #ffffff; border-radius: 22px; padding: 24px; box-shadow: 0 18px 40px rgba(0, 0, 0, 0.08); margin-bottom: 18px; }"
    ".feature-title { font-weight: 700; font-size: 1.1rem; margin-bottom: 8px; }"
    ".feature-text { color: #545b63; margin: 0; line-height: 1.6; }"
    ".streamlit-expanderHeader { font-weight: 700; }"
    "</style>",
    unsafe_allow_html=True,
)

st.sidebar.header("Telus International")
st.sidebar.write(
    "A clean task automation dashboard for your operations team. Select a date, generate tasks, and review results quickly."
)
st.sidebar.markdown(
    "**How to use:**\n- Choose a date from the calendar\n- Click Generate Tasks\n- Inspect output and logs below"
)

st.markdown(
    "<div class='hero-card'>"
    "<h1>Telus International Task Automation</h1>"
    "<p>Streamline daily task generation with a polished interface designed for Telus operations. Faster CSV review, status tracking, and clear action steps make your workflow simple.</p>"
    "</div>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("### Ready for today's tasks?")
    st.markdown(
        "<div class='feature-card'>"
        "<p class='feature-title'>Powerful automation</p>"
        "<p class='feature-text'>Select any date and generate task output from your CSV files instantly.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='feature-card'>"
        "<p class='feature-title'>Audit-ready reporting</p>"
        "<p class='feature-text'>View logs, capture errors, and verify output directly inside the app.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
with col2:
    st.metric(label="Company", value="Telus International", delta="Ready")
    st.metric(label="Mode", value="Task Automation", delta="Live")
    st.metric(label="Output", value="CSV + Tracker", delta="Included")

st.write("---")
st.write("### Select the date for task creation")
selected_date = st.date_input("Select Date", value=date.today())

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