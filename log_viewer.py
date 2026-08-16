"""
Real-time Log Viewer for RAG Pipeline
Displays execution logs with status, timestamps, and error tracking
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from logger_config import EXECUTION_LOG_DIR, ERROR_LOG_DIR, SUMMARY_LOG_DIR, ExecutionStatus

st.set_page_config(
    page_title="RAG Pipeline Logger",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .success-box { background-color: #D4EDDA; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #28A745; margin: 0.5rem 0; }
    .error-box { background-color: #F8D7DA; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #DC3545; margin: 0.5rem 0; }
    .warning-box { background-color: #FFF3CD; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #FFC107; margin: 0.5rem 0; }
    .info-box { background-color: #D1ECF1; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #17A2B8; margin: 0.5rem 0; }
    .code-box { background-color: #F5F5F5; padding: 1rem; border-radius: 0.5rem; font-family: monospace; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════════

st.sidebar.title("🔍 Log Viewer Settings")

view_type = st.sidebar.radio(
    "Select View:",
    ["📊 Execution Summary", "📁 Recent Executions", "❌ Error Logs", "📈 Statistics"]
)

auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)
if auto_refresh:
    import time
    time.sleep(5)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════════

def get_recent_executions(limit: int = 20) -> list:
    """Get recent execution logs"""
    logs = sorted(EXECUTION_LOG_DIR.glob("*_execution.json"), reverse=True)[:limit]
    return logs

def load_execution_log(file_path: Path) -> dict:
    """Load execution log from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading log: {e}")
        return {}

def get_status_color(status: str) -> str:
    """Get color for status"""
    if "SUCCESS" in status:
        return "green"
    elif "FAILED" in status:
        return "red"
    elif "PARTIAL" in status:
        return "orange"
    elif "SKIPPED" in status:
        return "gray"
    else:
        return "blue"

def format_stage_status(stages: dict) -> pd.DataFrame:
    """Format stages into DataFrame"""
    data = []
    for stage_name, stage_info in stages.items():
        data.append({
            "Stage": stage_name,
            "Status": stage_info.get("status", "Unknown"),
            "Duration (ms)": stage_info.get("duration_ms", "N/A"),
            "Error": stage_info.get("error", {}).get("message", "") if stage_info.get("error") else ""
        })
    return pd.DataFrame(data)

# ══════════════════════════════════════════════════════════════════════════════════
# MAIN TITLE
# ══════════════════════════════════════════════════════════════════════════════════

st.markdown("# 📊 RAG Pipeline Data Logger")
st.markdown("**Real-time monitoring of RAG pipeline execution**")

# ══════════════════════════════════════════════════════════════════════════════════
# VIEW 1: EXECUTION SUMMARY
# ══════════════════════════════════════════════════════════════════════════════════

if view_type == "📊 Execution Summary":
    st.header("Latest Execution Summary")
    
    recent = get_recent_executions(limit=1)
    if recent:
        log_data = load_execution_log(recent[0])
        summary = log_data.get("summary", {})
        stages = log_data.get("stages", {})
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "✅ SUCCESS" if summary.get("completed_successfully") else "❌ FAILED"
            st.metric("Status", status)
        
        with col2:
            st.metric("Duration", f"{summary.get('total_duration_seconds', 'N/A')}s")
        
        with col3:
            st.metric("Stages Completed", summary.get("total_stages", 0))
        
        with col4:
            answer_len = summary.get("answer_length", 0)
            st.metric("Answer Length", f"{answer_len} chars")
        
        st.divider()
        
        # Query and error info
        st.subheader("Query & Error Information")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input("Query", value=summary.get("query", ""), disabled=True)
        with col2:
            st.text_input("Exec ID", value=summary.get("execution_id", "")[-12:], disabled=True)
        
        if summary.get("error_stage"):
            st.markdown(f"""
<div class="error-box">
    <strong>⚠️ Error Detected</strong><br>
    <strong>Stage:</strong> {summary.get('error_stage')}<br>
    <strong>Message:</strong> {summary.get('error_message')}
</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="success-box">
    <strong>✅ Completed Successfully</strong><br>
    No errors encountered
</div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Stage breakdown
        st.subheader("Pipeline Stages Breakdown")
        
        df_stages = format_stage_status(stages)
        st.dataframe(df_stages, use_container_width=True)
        
        st.divider()
        
        # Answer info
        st.subheader("Answer Information")
        answer = log_data.get("final_answer", "")
        
        if answer:
            st.markdown(f"""
<div class="success-box">
    <strong>✅ Answer Generated</strong><br>
    Length: {len(answer)} characters
</div>
            """, unsafe_allow_html=True)
            st.text_area("Answer Preview", value=answer[:500] + "..." if len(answer) > 500 else answer, height=150, disabled=True)
        else:
            st.markdown(f"""
<div class="error-box">
    <strong>❌ No Answer Generated</strong>
</div>
            """, unsafe_allow_html=True)
    else:
        st.info("No execution logs found yet. Run the chatbot first!")

# ══════════════════════════════════════════════════════════════════════════════════
# VIEW 2: RECENT EXECUTIONS
# ══════════════════════════════════════════════════════════════════════════════════

elif view_type == "📁 Recent Executions":
    st.header("Recent Executions")
    
    recent = get_recent_executions(limit=20)
    
    if recent:
        executions_data = []
        for log_file in recent:
            log_data = load_execution_log(log_file)
            summary = log_data.get("summary", {})
            
            executions_data.append({
                "Execution ID": summary.get("execution_id", "")[-12:],
                "Query": summary.get("query", "")[:40],
                "Status": "✅ OK" if summary.get("completed_successfully") else "❌ ERROR",
                "Duration (s)": float(summary.get("total_duration_seconds", 0)),
                "Answer": "✅ Yes" if summary.get("answer_generated") else "❌ No",
                "Stages": f"{summary.get('total_stages', 0)}"
            })
        
        df = pd.DataFrame(executions_data)
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        
        # Click to view details
        selected_exec = st.selectbox(
            "Select execution to view details:",
            [f"{e[-12:]} - {q[:30]}" for e, q in zip([s.get("execution_id", "") for s in [load_execution_log(f).get("summary", {}) for f in recent]], 
                                                      [s.get("query", "") for s in [load_execution_log(f).get("summary", {}) for f in recent]])]
        )
        
        if selected_exec:
            idx = [f"{s.get('execution_id', '')[-12:]}" for s in [load_execution_log(f).get("summary", {}) for f in recent]].index(selected_exec.split(" ")[0])
            log_data = load_execution_log(recent[idx])
            summary = log_data.get("summary", {})
            
            st.subheader(f"Details - {summary.get('execution_id', '')}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", "✅ SUCCESS" if summary.get("completed_successfully") else "❌ FAILED")
            with col2:
                st.metric("Duration", f"{summary.get('total_duration_seconds', 'N/A')}s")
            with col3:
                st.metric("Answer Length", f"{summary.get('answer_length', 0)} chars")
            
            if summary.get("error_stage"):
                st.error(f"**Error in:** {summary.get('error_stage')}\n\n{summary.get('error_message')}")
    else:
        st.info("No execution logs found yet.")

# ══════════════════════════════════════════════════════════════════════════════════
# VIEW 3: ERROR LOGS
# ══════════════════════════════════════════════════════════════════════════════════

elif view_type == "❌ Error Logs":
    st.header("Error Logs")
    
    error_files = sorted(ERROR_LOG_DIR.glob("*_error.json"), reverse=True)[:20]
    
    if error_files:
        st.subheader(f"Total Errors: {len(error_files)}")
        
        for error_file in error_files:
            log_data = load_execution_log(error_file)
            summary = log_data.get("summary", {})
            stages = log_data.get("stages", {})
            
            with st.expander(f"❌ {summary.get('execution_id', '')[-12:]} - {summary.get('query', '')[:40]}..."):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Error Stage:** {summary.get('error_stage')}")
                    st.write(f"**Error Message:** {summary.get('error_message')}")
                
                with col2:
                    st.metric("Duration", f"{summary.get('total_duration_seconds', 'N/A')}s")
                
                # Show which stages passed before error
                st.write("**Stages Before Error:**")
                
                stages_before_error = []
                for stage_name, stage_info in stages.items():
                    if stage_name == summary.get('error_stage'):
                        break
                    status = stage_info.get("status", "")
                    if status == "✅ SUCCESS":
                        stages_before_error.append(f"✅ {stage_name}")
                
                if stages_before_error:
                    for stage in stages_before_error:
                        st.write(f"  {stage}")
                else:
                    st.write("  None - Error occurred in first stage")
    else:
        st.info("No errors found! 🎉")

# ══════════════════════════════════════════════════════════════════════════════════
# VIEW 4: STATISTICS
# ══════════════════════════════════════════════════════════════════════════════════

elif view_type == "📈 Statistics":
    st.header("Execution Statistics")
    
    recent = get_recent_executions(limit=100)
    
    if recent:
        # Calculate stats
        total_executions = len(recent)
        successful = 0
        failed = 0
        total_time = 0.0
        total_answers = 0
        
        for log_file in recent:
            log_data = load_execution_log(log_file)
            summary = log_data.get("summary", {})
            
            if summary.get("completed_successfully"):
                successful += 1
            else:
                failed += 1
            
            total_time += float(summary.get("total_duration_seconds", 0))
            if summary.get("answer_generated"):
                total_answers += 1
        
        # Display stats
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Executions", total_executions)
        
        with col2:
            success_rate = (successful / total_executions * 100) if total_executions > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            avg_time = total_time / total_executions if total_executions > 0 else 0
            st.metric("Avg Duration", f"{avg_time:.2f}s")
        
        with col4:
            st.metric("Total Successful", successful)
        
        with col5:
            answer_rate = (total_answers / total_executions * 100) if total_executions > 0 else 0
            st.metric("Answer Rate", f"{answer_rate:.1f}%")
        
        st.divider()
        
        # Charts
        st.subheader("Success vs Failure")
        
        status_data = {
            "Successful": successful,
            "Failed": failed
        }
        
        st.bar_chart(status_data)
    else:
        st.info("No data available for statistics.")

# ══════════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.8rem; padding: 2rem 0;">
    <p>RAG Pipeline Data Logger | Real-time Monitoring</p>
    <p>Logs stored in: <code>./logs/</code></p>
</div>
""", unsafe_allow_html=True)

