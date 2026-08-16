"""
Streamlit UI for BIT Jaipur RAG Assistant
FIXED: Uses rag_pipeline_dual_llm for proper model switching
FIXED: Model selection works via LLM_CHOICE env var
"""

import streamlit as st
import sys
import os
import time
import csv
from pathlib import Path
from datetime import datetime

import uuid

# Create session ID once
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ══════════════════════════════════════════════════════════════════
# MODEL SELECTION (Add this to your sidebar)
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 🤖 Model Selection")
    
    from model_manager import model_manager
    
    # ✅ FIX: Use session state to persist model selection across reruns
    if "selected_model_ui" not in st.session_state:
        st.session_state.selected_model_ui = model_manager.get_current_model()
    
    available_models = dict(model_manager.get_all_models())
    
    selected_model = st.selectbox(
        "Choose Model:",
        options=list(available_models.keys()),
        format_func=lambda x: available_models[x],
        index=list(available_models.keys()).index(st.session_state.selected_model_ui),
        help="Switch between Ollama (local) and Groq (API)"
    )
    
    # ✅ FIX: Update BOTH session state AND model_manager AND env var
    if selected_model != st.session_state.selected_model_ui:
        st.session_state.selected_model_ui = selected_model
        if model_manager.set_current_model(selected_model):
            # Also update env var for rag_pipeline_dual_llm to read
            llm_choice = "groq" if selected_model == "llama-3.3-70b-versatile" else "ollama"
            os.environ["LLM_CHOICE"] = llm_choice
            st.success(f"✅ Switched to {model_manager.get_current_model_name()}")
        else:
            st.error(f"❌ Failed to switch")
    else:
        # ✅ FIX: Also update model_manager on every rerun to be safe
        model_manager.set_current_model(selected_model)
        llm_choice = "groq" if selected_model == "llama-3.3-70b-versatile" else "ollama"
        os.environ["LLM_CHOICE"] = llm_choice
    
    if selected_model == "llama-3.3-70b-versatile":
        if not model_manager.groq_api_key:
            st.error("❌ Groq API key not found in .env")
        else:
            st.success("✅ Groq API key found")
    
    st.divider()
    st.markdown("#### Current Model Info")
    model_info = model_manager.get_model_info(model_manager.get_current_model())
    st.caption(f"**Provider:** {model_info['provider'].upper()}")
    st.caption(f"**Speed:** {model_info['speed']}")
    st.caption(f"**Cost:** {model_info['cost']}")
    st.caption(model_info['description'])

# ══════════════════════════════════════════════════════════════════════════════════
# TERMINAL OUTPUT FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════════

class Colors:
    """Terminal color codes"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    CYAN = '\033[36m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'


def print_terminal_header():
    """Print welcome header to terminal"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("🎓 BIT JAIPUR ASSISTANT - TERMINAL OUTPUT WITH STREAMING")
    print("=" * 80)
    print(f"{Colors.RESET}")
    print(f"{Colors.DIM}Session started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.DIM}Real-time answer streaming ENABLED ✨{Colors.RESET}")
    print(f"{Colors.DIM}Outputs will appear here as you interact with the Streamlit UI{Colors.RESET}\n")


def print_user_query(query: str, query_num: int = 1):
    """Print user query to terminal"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}[Query #{query_num}] {datetime.now().strftime('%H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BOLD}👤 User:{Colors.RESET}")
    print(f"   {Colors.CYAN}{query}{Colors.RESET}\n")


def print_assistant_response(response_data: dict, response_num: int = 1):
    """Print full assistant response to terminal with all metadata"""
    
    print(f"{Colors.BOLD}{Colors.GREEN}[Response #{response_num}]{Colors.RESET}")
    print(f"{Colors.BOLD}🤖 Assistant:{Colors.RESET}")
    
    # Answer content - check content key first (Streamlit uses this)
    if "content" in response_data:
        answer = response_data["content"]
    elif "answer" in response_data:
        answer = response_data["answer"]
    else:
        answer = "No answer generated"
    
    # Make sure answer is not empty
    if answer and answer.strip():
        for line in answer.split('\n'):
            if line.strip():  # Only print non-empty lines
                print(f"   {line}")
    else:
        print(f"   {Colors.RED}[No content available]{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}📊 Response Metadata:{Colors.RESET}")
    
    # Time
    elapsed_time = response_data.get("time", 0)
    time_str = format_time_terminal(elapsed_time)
    print(f"   {Colors.YELLOW}⏱️  Time: {time_str}{Colors.RESET}")
    
    # Model
    model = response_data.get("model", "Unknown")
    print(f"   {Colors.YELLOW}🤖 Model: {model}{Colors.RESET}")
    
    # Intent
    intent = response_data.get("intent", "unknown").upper()
    intent_emoji = get_intent_emoji(intent)
    print(f"   {Colors.YELLOW}{intent_emoji} Intent: {intent}{Colors.RESET}")
    
    # History Used
    history_used = response_data.get("history_used", False)
    history_str = f"{Colors.GREEN}✅ Yes{Colors.RESET}" if history_used else f"{Colors.RED}❌ No{Colors.RESET}"
    print(f"   {Colors.YELLOW}📚 History Used: {history_str}{Colors.RESET}")
    
    # Prompt Type
    prompt_type = response_data.get("prompt_type", "UNKNOWN")
    prompt_emoji = "📝" if "INFORMATION" in prompt_type else "💬"
    print(f"   {Colors.YELLOW}{prompt_emoji} Prompt Type: {prompt_type}{Colors.RESET}")
    
    # Sources
    sources = response_data.get("sources", [])
    if sources:
        print(f"\n   {Colors.BOLD}📎 Sources (Top {len(sources)} chunks):{Colors.RESET}")
        for i, source in enumerate(sources, 1):
            title = source.get("title", "Unknown")
            section = source.get("section", "")
            score = source.get("score", 0)
            section_str = f" - {section}" if section else ""
            
            print(f"      {i}. {Colors.CYAN}{title}{section_str}{Colors.RESET}")
            print(f"         {Colors.DIM}Relevance: {score:.1%}{Colors.RESET}")
    
    # Full Chunk Content
    chunks_content = response_data.get("chunks_content", [])
    if chunks_content:
        print(f"\n   {Colors.BOLD}{Colors.BLUE}📖 Full Chunk Content from Qdrant:{Colors.RESET}")
        print(f"   {Colors.DIM}{'─' * 76}{Colors.RESET}")
        
        for i, chunk in enumerate(chunks_content, 1):
            title = chunk.get("title", "Unknown")
            section = chunk.get("section", "")
            score = chunk.get("score", 0)
            content = chunk.get("content", "No content available")
            chunk_id = chunk.get("id", "")
            
            section_str = f" - {section}" if section else ""
            
            print(f"\n      {Colors.BOLD}Chunk {i}: {Colors.CYAN}{title}{section_str}{Colors.RESET}")
            print(f"      {Colors.YELLOW}📊 Relevance: {score:.1%} | ID: {chunk_id}{Colors.RESET}")
            print(f"      {Colors.DIM}Content:{Colors.RESET}")
            
            # Print content with indentation
            for line in content.split('\n'):
                if line.strip():
                    print(f"         {line}")
            
            print(f"      {Colors.DIM}{'─' * 72}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'─' * 80}{Colors.RESET}\n")


def format_time_terminal(seconds: float) -> str:
    """Format time nicely for terminal"""
    if seconds < 1:
        return f"⚡ {seconds:.2f}s"
    elif seconds < 5:
        return f"🚀 {seconds:.1f}s"
    elif seconds < 10:
        return f"⭐ {seconds:.1f}s"
    elif seconds < 60:
        return f"⏱️  {seconds:.1f}s"
    else:
        mins = seconds / 60
        return f"⏳ {mins:.1f}m"


def get_intent_emoji(intent: str) -> str:
    """Get emoji for intent type"""
    intent_map = {
        "ADMISSION": "📋",
        "EXPLORING": "🔍",
        "UNDECIDED": "🤔",
        "REJECTION": "❌",
        "CASUAL": "💬",
        "GENERAL": "❓"
    }
    return intent_map.get(intent, "❓")


def print_statistics(total_queries: int, total_responses: int, avg_time: float = 0):
    """Print session statistics to terminal"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}")
    print("=" * 80)
    print("📊 SESSION STATISTICS")
    print("=" * 80)
    print(f"{Colors.RESET}")
    
    if total_queries > 0:
        print(f"   {Colors.CYAN}Total Queries: {Colors.WHITE}{total_queries}{Colors.RESET}")
        print(f"   {Colors.CYAN}Total Responses: {Colors.WHITE}{total_responses}{Colors.RESET}")
        if avg_time > 0:
            print(f"   {Colors.CYAN}Average Response Time: {Colors.WHITE}{format_time_terminal(avg_time)}{Colors.RESET}")
    else:
        print(f"   {Colors.CYAN}No queries yet. Ask a question to get started!{Colors.RESET}")
    
    print(f"\n{Colors.RESET}")


# ══════════════════════════════════════════════════════════════════════════════════
# CACHE PIPELINE IMPORT - Uses rag_pipeline_dual_llm for proper model switching
# ══════════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def load_pipeline():
    """Load RAG pipeline only once"""
    # ✅ FIXED: Use rag_pipeline_dual_llm which reads LLM_CHOICE from env
    from rag_pipeline_dual import (
        ask,
        detect_intent,
        retrieve_chunks,
        build_context_enhanced,
        SYSTEM_PROMPT_INFORMATION_FIRST,
        SYSTEM_PROMPT_CASUAL_FRIENDLY
    )
    
    return ask, detect_intent, retrieve_chunks, build_context_enhanced, SYSTEM_PROMPT_INFORMATION_FIRST, SYSTEM_PROMPT_CASUAL_FRIENDLY

ask, detect_intent, retrieve_chunks, build_context_enhanced, SYSTEM_PROMPT_INFORMATION_FIRST, SYSTEM_PROMPT_CASUAL_FRIENDLY = load_pipeline()

# Import logger wrapper (with logging support)
try:
    from logger_wrapper import ask_with_logging
except ImportError:
    # Fallback: use regular ask() function if logger not available
    ask_with_logging = ask

# ══════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════════

def get_conversation_history():
    """Get conversation history from session state."""
    conversation = []
    for msg in st.session_state.messages:
        conversation.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    return conversation


def format_response_time(elapsed_seconds: float) -> str:
    """Format elapsed time in a human-readable way."""
    if elapsed_seconds < 1:
        return f"⚡ {elapsed_seconds:.2f}s"
    elif elapsed_seconds < 5:
        return f"🚀 {elapsed_seconds:.1f}s"
    elif elapsed_seconds < 10:
        return f"⭐ {elapsed_seconds:.1f}s"
    else:
        return f"⏱️ {elapsed_seconds:.1f}s"


def compute_retrieval_confidence(chunks: list) -> dict:
    """Confidence based on how well the knowledge base actually matched
    the query -- the average Qdrant similarity score of the chunks that
    were used. This is NOT a measure of whether the answer is correct
    (a chunk can match well and still contain wrong/stale information --
    see the CSE HOD case). It's a measure of retrieval quality only.
    """
    if not chunks:
        return {"label": "No Match", "pct": 0.0, "color": "#D32F2F"}

    scores = [c.get("score", 0) for c in chunks]
    avg_score = sum(scores) / len(scores)

    if avg_score >= 0.60:
        label, color = "High", "#2E7D32"
    elif avg_score >= 0.45:
        label, color = "Medium", "#F9A825"
    else:
        label, color = "Low", "#D32F2F"

    return {"label": label, "pct": avg_score, "color": color}


def display_confidence_meter(confidence: dict):
    if confidence is None:
        return
    pct = confidence["pct"]
    st.markdown(f"""
<div style="margin: 0.3rem 0 0.6rem 0;">
    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #555; margin-bottom: 0.2rem;">
        <span>🎯 Retrieval Confidence: <strong style="color: {confidence['color']};">{confidence['label']}</strong></span>
        <span>{pct:.0%}</span>
    </div>
    <div style="background-color: #EEE; border-radius: 1rem; height: 0.5rem; overflow: hidden;">
        <div style="background-color: {confidence['color']}; width: {pct*100:.0f}%; height: 100%;"></div>
    </div>
</div>
    """, unsafe_allow_html=True)


FEEDBACK_LOG_PATH = Path("feedback_log.csv")
FEEDBACK_LOG_FIELDS = ["timestamp", "session_id", "query", "model", "intent",
                       "prompt_type", "confidence_label", "confidence_pct", "rating"]


def save_feedback(query, model, intent, prompt_type, confidence, rating):
    """Append one feedback row (rating is 'correct' or 'incorrect').
    Creates the CSV with a header the first time it's called. This file
    accumulates across every session/day it's run, so it's the source
    for computing real accuracy over time -- see notes below on how to
    analyze it."""
    is_new = not FEEDBACK_LOG_PATH.exists()
    with open(FEEDBACK_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEEDBACK_LOG_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(),
            "session_id": st.session_state.get("session_id", ""),
            "query": query,
            "model": model,
            "intent": intent,
            "prompt_type": prompt_type,
            "confidence_label": confidence["label"] if confidence else "",
            "confidence_pct": f"{confidence['pct']:.3f}" if confidence else "",
            "rating": rating,
        })


def display_feedback_buttons(msg, msg_index):
    """👍/👎 under each answer. Once rated, shows a thank-you instead of
    the buttons again (rating is stored on the message so it persists
    across reruns within the session)."""
    existing = msg.get("feedback")
    if existing:
        label = "correct" if existing == "correct" else "incorrect"
        st.caption(f"✅ Marked as **{label}** -- thanks for the feedback!")
        return

    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button("👍", key=f"fb_up_{msg_index}"):
            save_feedback(
                msg.get("query_for_feedback", ""), msg.get("model", ""),
                msg.get("intent", ""), msg.get("prompt_type", ""),
                msg.get("confidence"), "correct"
            )
            st.session_state.messages[msg_index]["feedback"] = "correct"
            st.rerun()
    with col2:
        if st.button("👎", key=f"fb_down_{msg_index}"):
            save_feedback(
                msg.get("query_for_feedback", ""), msg.get("model", ""),
                msg.get("intent", ""), msg.get("prompt_type", ""),
                msg.get("confidence"), "incorrect"
            )
            st.session_state.messages[msg_index]["feedback"] = "incorrect"
            st.rerun()


def get_session_accuracy():
    """Accuracy from feedback given so far THIS session (from
    session_state, not the CSV, so it updates live without a file read).
    Returns None if nothing's been rated yet."""
    rated = [m for m in st.session_state.messages if m.get("feedback")]
    if not rated:
        return None
    correct = sum(1 for m in rated if m["feedback"] == "correct")
    return correct / len(rated), len(rated)


def display_response_stats(elapsed_time: float, model_used: str, history_used: bool, prompt_type: str):
    """Display response statistics - SAME AS BEFORE"""
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        time_str = format_response_time(elapsed_time)
        st.caption(f"⏱️ {time_str}")
    
    with col2:
        if model_used and model_used != "none":
            if "gemma" in model_used.lower():
                st.caption(f"🟢 Gemma 4 e2b")
            else:
                st.caption(f"🔵 Llama 3.3-70b")
    
    with col3:
        history_indicator = "✅ Yes" if history_used else "❌ No"
        st.caption(f"📚 History: {history_indicator}")
    
    with col4:
        prompt_emoji = "📝" if "INFORMATION" in prompt_type else "💬"
        st.caption(f"{prompt_emoji} {prompt_type}")


def display_messages():
    """Display all messages - OPTIMIZED but SAME STYLE"""
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        
        else:  # assistant
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])

                # Retrieval confidence meter
                if "confidence" in msg:
                    display_confidence_meter(msg["confidence"])
                
                # Display stats if available
                if "time" in msg:
                    display_response_stats(
                        msg.get("time", 0),
                        msg.get("model", ""),
                        msg.get("history_used", False),
                        msg.get("prompt_type", "")
                    )

                # Was this answer right or wrong?
                if "time" in msg:
                    display_feedback_buttons(msg, idx)
                
                # Display sources with metadata if available
                if msg.get("sources"):
                    with st.expander("📎 Sources (Metadata)", expanded=False):
                        for i, source in enumerate(msg["sources"], 1):
                            section_info = f" - {source['section']}" if source.get("section") else ""
                            st.markdown(f"""
<div style="background-color: #FFF9E6; padding: 0.8rem; margin: 0.4rem 0; border-left: 3px solid #FFC107; border-radius: 0.25rem; font-size: 0.9rem;">
    <strong>Source {i}: {source['title']}{section_info}</strong>
    <div style="font-size: 0.8rem; color: #666; margin-top: 0.2rem;">Relevance Score: {source['score']:.1%}</div>
</div>
                            """, unsafe_allow_html=True)
                
                # Display full chunk content if available
                if msg.get("chunks_content"):
                    with st.expander("📖 Full Chunk Content (Retrieved from Qdrant)", expanded=False):
                        for i, chunk in enumerate(msg["chunks_content"], 1):
                            title = chunk.get("title", "Unknown")
                            section = chunk.get("section", "")
                            score = chunk.get("score", 0)
                            content = chunk.get("content", "No content available")
                            source_id = chunk.get("id", "")
                            
                            section_str = f" - {section}" if section else ""
                            source_id_str = f" (ID: {source_id})" if source_id else ""
                            
                            # Create a nice card for each chunk
                            st.markdown(f"""
<div style="background-color: #E3F2FD; padding: 1rem; margin: 1rem 0; border-left: 4px solid #1976D2; border-radius: 0.5rem;">
    <div style="margin-bottom: 0.5rem;">
        <strong style="font-size: 1.1rem; color: #1976D2;">Chunk {i}: {title}{section_str}</strong>
        <div style="font-size: 0.85rem; color: #666; margin-top: 0.3rem;">
            📊 Relevance: <span style="color: #2E7D32; font-weight: bold;">{score:.1%}</span> | Qdrant ID: <code style="background-color: #F5F5F5; padding: 0.2rem 0.4rem; border-radius: 0.2rem;">{source_id_str}</code>
        </div>
    </div>
    <div style="background-color: #FFFFFF; padding: 0.8rem; border-radius: 0.3rem; margin-top: 0.5rem; border: 1px solid #BBDEFB; font-family: 'Courier New', monospace; font-size: 0.9rem; line-height: 1.5; color: #333; white-space: pre-wrap;">
{content}
    </div>
</div>
                            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="BIT Jaipur Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main layout */
    .main {
        padding: 1rem 2rem;
    }
    
    /* Header - COMPACT */
    .header {
        text-align: center;
        margin-bottom: 0.5rem;
        padding: 0.5rem 0;
    }
    
    .header h1 {
        font-size: 1.8rem;
        margin: 0;
        color: #1f1f1f;
        font-weight: 700;
    }
    
    .header p {
        font-size: 0.85rem;
        color: #666;
        margin: 0.2rem 0 0 0;
    }
    
    /* Sources */
    .source-item {
        background-color: #FFF9E6;
        padding: 0.8rem;
        margin: 0.4rem 0;
        border-left: 3px solid #FFC107;
        border-radius: 0.25rem;
        font-size: 0.9rem;
    }
    
    .source-item strong {
        display: block;
        margin-bottom: 0.4rem;
        color: #1f1f1f;
    }
    
    .source-score {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.2rem;
    }
    
    /* Intent Badge */
    .intent-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════════
# SESSION STATE & TERMINAL OUTPUT
# ══════════════════════════════════════════════════════════════════════════════════

if "messages" not in st.session_state:
    st.session_state.messages = []

if "terminal_enabled" not in st.session_state:
    st.session_state.terminal_enabled = True

if "terminal_initialized" not in st.session_state:
    st.session_state.terminal_initialized = False
    print_terminal_header()
    st.session_state.terminal_initialized = True


# ══════════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Terminal Output Option
    st.markdown("#### 🖥️ Terminal Output")
    st.session_state.terminal_enabled = st.checkbox(
        "Show output in terminal/console",
        value=st.session_state.terminal_enabled,
        help="Displays all interactions in the terminal where Streamlit is running"
    )
    
    if st.session_state.terminal_enabled:
        st.info("✅ Terminal output is **ENABLED**\n✨ Real-time streaming is **ACTIVE**\nCheck your terminal to see detailed logs!")
    
    st.divider()
    
    # About Section
    st.markdown("#### 📖 About")
    st.markdown("""
    **BIT Jaipur Assistant** is a conversational AI chatbot powered by:
    - 🤖 **Gemma 4 e2b / Llama 3.3-70b**
    - 🗂️ Qdrant Vector Database
    - 🧠 RAG Pipeline
    - 🎯 Smart Intent Detection
    - 💬 Dual Prompt System
    """)
    
    st.divider()
    
    # Advanced Features
    st.markdown("#### ✨ Advanced Features")
    
    with st.expander("Dual Model Support", expanded=False):
        st.markdown("""
**Switch between models:**
- 🟢 Gemma 4 e2b (Ollama - Local)
- 🔵 Llama 3.3-70b (Groq - API)
- Real-time streaming
- Dynamic model switching
        """)
    
    with st.expander("Smart Conversation Memory", expanded=False):
        st.markdown("""
**Intelligent history tracking:**
- Remembers last 5 Q&A pairs
- Forgets older context
- Prevents hallucination
- Focus on current topic
        """)
    
    with st.expander("Keyword Matching", expanded=False):
        st.markdown("""
**Smart context awareness:**
- Uses history only when relevant
- Fresh answers for new topics
- No unnecessary context
- Better focus
        """)
    
    with st.expander("Foul Language Detection", expanded=False):
        st.markdown("""
**Safety features:**
- Detects vulgar language
- Refuses disrespectful content
- Maintains respectful tone
        """)
    
    with st.expander("Dual Prompt System", expanded=False):
        st.markdown("""
**Two intelligent prompts:**
1️⃣ **Information-First** - For admission, exploring, undecided
2️⃣ **Casual-Friendly** - For casual chat, rejection
        """)
    
    st.divider()
    
    # Sample Questions
    st.markdown("#### 💡 Sample Questions")
    sample_questions = [
        ("What programmes are offered?", "📝 Admission"),
        ("What is the placement record?", "📊 Admission"),
        ("How do I apply?", "📋 Admission"),
        ("Who is the Director of BIT Jaipur?", "👥 Director"),
        ("Tell me about campus life", "🔍 Exploring"),
        ("I'm not sure about applying", "🤔 Undecided"),
        ("Hi, how are you?", "💬 Casual"),
    ]
    
    for question, label in sample_questions:
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(question, key=f"sample_{question}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()
        with col2:
            st.caption(label)


# ══════════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="header">
    <h1>🎓 BIT Jaipur Campus Assistant</h1>
    <p>Smart, conversational assistant with advanced context awareness & dual prompts</p>
    <p style="font-size: 0.75rem; color: #999; margin: 0.5rem 0 0 0;">✨ Real-time streaming enabled | 💻 Terminal output enabled | Check your console for live logs</p>
</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("### 💬 Chat")
messages_container = st.container()

with messages_container:
    display_messages()


# ══════════════════════════════════════════════════════════════════════════════════
# OPTIMIZED RESPONSE GENERATION WITH TERMINAL OUTPUT + STREAMING
# ══════════════════════════════════════════════════════════════════════════════════

# Check if we need to generate a response for the last user message
if st.session_state.messages:
    last_message = st.session_state.messages[-1]
    
    # If last message is from user and doesn't have a response yet
    if last_message["role"] == "user" and "time" not in last_message:
        st.divider()
        
        # Count queries/responses for terminal output
        user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
        
        # Print to terminal
        if st.session_state.terminal_enabled:
            print_user_query(last_message["content"], user_msgs)
        
        # Show generating indicator
        with st.spinner("🔍 Analyzing intent, checking history, and generating answer..."):
            try:
                user_question = last_message["content"]
                
                # Get conversation history (exclude current message)
                conversation_history = get_conversation_history()[:-1]
                
                # TRACK RESPONSE TIME
                start_time = time.time()
                
                # Call RAG pipeline WITH STREAMING ENABLED
                result = ask_with_logging(
                    user_question,
                    conversation_history=conversation_history,
                    session_id=st.session_state.session_id if "session_id" in st.session_state else "session_1",
                    timeout=600,
                    show_streaming=True  # ✨ ENABLE REAL-TIME STREAMING IN TERMINAL
                )
                
                elapsed_time = time.time() - start_time
                
                # Extract response
                answer = result["answer"]
                intent = result["intent"]
                model_used = result["model_used"]
                history_used = result.get("history_used", False)
                prompt_type = result.get("prompt_type", "UNKNOWN")
                sources = [
                    {
                        "title": c["title"],
                        "section": c.get("section", ""),
                        "score": c["score"]
                    }
                    for c in result.get("chunks", [])
                ]
                
                # Also store full chunk content for detailed display
                chunks_content = [
                    {
                        "title": c["title"],
                        "section": c.get("section", ""),
                        "score": c["score"],
                        "content": c.get("content", "No content available"),
                        "id": c.get("id", "")
                    }
                    for c in result.get("chunks", [])
                ]

                confidence = compute_retrieval_confidence(result.get("chunks", []))
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                answer = f"❌ Error: {str(e)}\n\nDetails: {error_detail[:500]}"
                intent = "general"
                model_used = "none"
                history_used = False
                prompt_type = "ERROR"
                sources = []
                chunks_content = []
                elapsed_time = 0
                confidence = None
        
        # Add assistant message with tracking info
        assistant_msg = {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "chunks_content": chunks_content,
            "intent": intent,
            "model": model_used,
            "history_used": history_used,
            "prompt_type": prompt_type,
            "time": elapsed_time,
            "confidence": confidence,
            "query_for_feedback": user_question,
        }
        
        st.session_state.messages.append(assistant_msg)
        
        # Print to terminal
        if st.session_state.terminal_enabled:
            print_assistant_response(assistant_msg, user_msgs)
        
        # Rerun to display the response
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════════
# INPUT AREA
# ══════════════════════════════════════════════════════════════════════════════════

st.divider()

with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask about BIT Jaipur...",
            placeholder="Type your question and press Enter or click Send",
            label_visibility="collapsed"
        )
    
    with col2:
        submit_button = st.form_submit_button("↑", use_container_width=True)
    
    # Process form submission
    if submit_button and user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════════

st.divider()

st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.8rem; padding: 0.5rem 0;">
    <p style="margin: 0;">Built with ❤️ for BIT Mesra Jaipur | Powered by Gemma 4 e2b + Llama 3.3-70b + Advanced RAG + Real-time Streaming</p>
    <p style="margin: 0.3rem 0 0 0; font-size: 0.7rem;">✨ Real-time streaming enabled | 🖥️ Terminal output enabled | Check console for live streaming output</p>
</div>
""", unsafe_allow_html=True)

# Utilities Row
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        print(f"\n{Colors.YELLOW}[Terminal] Chat cleared by user{Colors.RESET}\n")
        st.rerun()

with col2:
    # Show conversation stats
    if st.session_state.messages:
        user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
        bot_msgs = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
        st.caption(f"💬 {user_msgs} Q | 🤖 {bot_msgs} A")

with col3:
    # Show intent stats if available
    if st.session_state.messages:
        intents = [m.get("intent", "unknown") for m in st.session_state.messages if m.get("intent")]
        if intents:
            most_common_intent = max(set(intents), key=intents.count)
            st.caption(f"🎯 {most_common_intent.title()}")

with col4:
    # Live accuracy from 👍/👎 feedback given so far this session
    accuracy_result = get_session_accuracy()
    if accuracy_result:
        acc_pct, n_rated = accuracy_result
        st.caption(f"✅ {acc_pct:.0%} accurate ({n_rated} rated)")
    else:
        st.caption("✅ No feedback yet")