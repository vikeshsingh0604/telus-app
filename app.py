import streamlit as st
from datetime import datetime
import os
import sys
import pandas as pd
import runpy
import io
import contextlib

st.set_page_config(page_title="Task Automation - Telus Digital", layout="wide", page_icon=None)

# --- Branding and simple theme ---
PRIMARY = "#6DBE45"
SECONDARY = "#262626"

def _local_logo_path():
    # prefer local logo if present
    for candidate in ["logo.png", "telus_logo.png", "telus.png"]:
        if os.path.exists(candidate):
            return candidate
    return None

logo_path = _local_logo_path()

st.markdown(
    f"""
    <style>
    :root {{ --primary: {PRIMARY}; --secondary: {SECONDARY}; }}
    .td-header {{ display:flex; align-items:center; gap:12px; }}
    .td-title {{ font-size:28px; font-weight:700; color:var(--secondary); margin:0; }}
    .td-sub {{ color:#444; margin:0; }}
    .td-card {{ border-radius:10px; padding:12px; background:linear-gradient(90deg, rgba(255,255,255,0.8), rgba(245,245,245,0.8)); box-shadow:0 4px 14px rgba(0,0,0,0.06); margin-bottom:10px }}
    .td-pill {{ display:inline-block; padding:4px 8px; border-radius:999px; background:var(--primary); color:white; font-weight:600; font-size:12px }}
    .td-small {{ color:#666; font-size:13px }}
    .stButton>button { background: var(--primary); color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([0.12, 0.88])
with col1:
    if logo_path:
        st.image(logo_path, width=80)
    else:
        st.write("")
with col2:
    st.markdown('<div class="td-header">', unsafe_allow_html=True)
    st.markdown('<div>')
    st.markdown('<h1 class="td-title">Task Automation — Telus Digital</h1>', unsafe_allow_html=True)
    st.markdown('<p class="td-sub">Generate and review scheduled tasks with live logs and retry options.</p>', unsafe_allow_html=True)
    st.markdown('</div>')
    st.markdown('</div>')

# Controls in sidebar for a compact, branded layout
selected_date = st.sidebar.date_input("Select Date", value=datetime.today())
st.sidebar.markdown("---")
st.sidebar.caption("Tip: Use the button below to generate tasks for the selected date.")

if st.sidebar.button("Generate Tasks"):

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

        # Render tasks as compact cards for better readability
        st.markdown("### Today's Tasks")
        for _, r in df.iterrows():
            client = r.get("Clients", "")
            process = r.get("Process", "")
            sched = r.get("Scheduled Day", "")
            tat = r.get("TAT", "")
            aht = r.get("Process AHT", "")
            peer = r.get("Peer review AHT", "")
            with st.container():
                st.markdown('<div class="td-card">', unsafe_allow_html=True)
                cols = st.columns([0.02, 0.6, 0.38])
                cols[1].markdown(f"**{client}**  ")
                cols[1].markdown(f"**{process}**  \n<span class=\"td-small\">{sched} · {tat}</span>", unsafe_allow_html=True)
                cols[2].markdown(f"<div style=\"text-align:right\"> <span class=\"td-pill\">AHT: {aht}</span> <div class=\"td-small\">Peer: {peer}</div></div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.warning("No output file was generated. Please verify the logs and try again.")

    # If a previous Google Sheets update failed, a fallback CSV may exist
    pending_file = "pending_tracker_update.csv"
    if os.path.exists(pending_file):
        st.warning(f"A pending Google Sheets update exists: {pending_file}")
        if st.button("Retry Google Sheets Upload"):
            stdout_buf2 = io.StringIO()
            stderr_buf2 = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout_buf2), contextlib.redirect_stderr(stderr_buf2):
                    runpy.run_path("push_pending.py", run_name="__main__")
                st.success("Retry completed — see logs below.")
            except SystemExit as e:
                stderr_buf2.write(f"SystemExit: {e}\n")
                st.error(f"Retry script exited: {e}")
            except Exception as e:
                stderr_buf2.write(str(e) + "\n")
                st.error(f"Retry failed: {e}")

            st.subheader("Retry Logs")
            out = stdout_buf2.getvalue()
            err = stderr_buf2.getvalue()
            if out:
                st.code(out.strip(), language="bash")
            if err:
                st.code(err.strip(), language="bash")
            if not out and not err:
                st.write("No logs produced by retry.")