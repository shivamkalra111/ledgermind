# LedgerMind Streamlit UI
"""
Internal tool for testing the API.

Features:
- Persistent login (survives refresh)
- File management panel
- ChatGPT-style chat interface

Run:
    1. Start API: uvicorn api.app:app --port 8000
    2. Start UI:  streamlit run streamlit/app.py
"""

import streamlit as st
import requests
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Configuration
# =============================================================================

API_BASE_URL = "http://localhost:8000"


# =============================================================================
# Page Config
# =============================================================================

st.set_page_config(
    page_title="LedgerMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# Custom CSS for ChatGPT-like UI
# =============================================================================

st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
    }
    
    .assistant-message {
        background: #f0f2f6;
        color: #1f1f1f;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
    }
    
    /* File cards */
    .file-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    
    /* Login card */
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State Initialization
# =============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "customer_id" not in st.session_state:
    st.session_state.customer_id = None
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_files" not in st.session_state:
    st.session_state.show_files = True


# =============================================================================
# API Helper Functions
# =============================================================================

def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200, response.json()
    except:
        return False, {}


def validate_login(customer_id: str, api_key: str) -> tuple:
    """Validate API key by making a test request."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/files",
            headers={"X-API-Key": api_key},
            timeout=5
        )
        if response.status_code == 200:
            return True, "Login successful"
        elif response.status_code == 401:
            return False, "Invalid API key"
        else:
            return False, f"Error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "API not running"
    except Exception as e:
        return False, str(e)


def api_query(query: str) -> dict:
    """Send query to API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/query",
            headers={"X-API-Key": st.session_state.api_key},
            json={"query": query},
            timeout=120
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"success": False, "answer": "❌ API not running"}
    except Exception as e:
        return {"success": False, "answer": f"❌ Error: {str(e)}"}


def api_upload(files) -> dict:
    """Upload files via API."""
    try:
        files_data = [("files", (f.name, f.read(), "application/octet-stream")) for f in files]
        response = requests.post(
            f"{API_BASE_URL}/api/v1/upload",
            headers={"X-API-Key": st.session_state.api_key},
            files=files_data,
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def api_list_files() -> dict:
    """List files via API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/files",
            headers={"X-API-Key": st.session_state.api_key},
            timeout=10
        )
        return response.json()
    except:
        return {"success": False, "files": []}


def api_delete_file(filename: str) -> dict:
    """Delete file via API."""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/v1/files/{filename}",
            headers={"X-API-Key": st.session_state.api_key},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


# =============================================================================
# Login Screen
# =============================================================================

def show_login():
    """Display login screen."""
    
    # Check API status
    api_ok, health = check_api_health()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🧠 LedgerMind")
        st.markdown("### AI CFO for MSMEs")
        
        st.divider()
        
        # API Status
        if api_ok:
            llm_status = "✅" if health.get("llm_available") else "⚠️"
            st.success(f"API Online | LLM: {llm_status}")
        else:
            st.error("❌ API Offline")
            st.code("uvicorn api.app:app --port 8000", language="bash")
            st.stop()
        
        st.markdown("### Login")
        
        with st.form("login_form"):
            customer_id = st.text_input(
                "Customer ID",
                placeholder="e.g., sample_company"
            )
            
            api_key = st.text_input(
                "API Key",
                type="password",
                placeholder="lm_test_easy_key_12345"
            )
            
            submitted = st.form_submit_button("🔐 Login", use_container_width=True)
            
            if submitted:
                if not customer_id or not api_key:
                    st.error("Please enter both Customer ID and API Key")
                else:
                    with st.spinner("Verifying..."):
                        success, message = validate_login(customer_id, api_key)
                    
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.customer_id = customer_id
                        st.session_state.api_key = api_key
                        st.session_state.chat_history = []
                        st.rerun()
                    else:
                        st.error(f"Login failed: {message}")
        
        st.divider()
        st.caption("Test credentials: `sample_company` / `lm_test_easy_key_12345`")


# =============================================================================
# Main App (After Login)
# =============================================================================

def show_main_app():
    """Display main application after login."""
    
    # Sidebar
    with st.sidebar:
        # User info & logout
        st.markdown(f"### 👤 {st.session_state.customer_id}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.customer_id = None
            st.session_state.api_key = None
            st.session_state.chat_history = []
            st.rerun()
        
        st.divider()
        
        # File Upload
        st.markdown("### 📁 Your Files")
        
        uploaded = st.file_uploader(
            "Upload",
            type=["xlsx", "xls", "csv"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if uploaded:
            if st.button("📤 Upload Files", use_container_width=True):
                with st.spinner("Uploading..."):
                    result = api_upload(uploaded)
                if result.get("success"):
                    st.success(f"✅ {result.get('files_uploaded', 0)} file(s) uploaded")
                    st.rerun()
                else:
                    st.error(result.get("message", "Upload failed"))
        
        st.divider()
        
        # File List
        files_data = api_list_files()
        files = files_data.get("files", [])
        
        if files:
            for f in files:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**📄 {f['name']}**")
                        info = f"{f['size_kb']:.1f} KB"
                        if f.get('row_count'):
                            info += f" • {f['row_count']} rows"
                        st.caption(info)
                    with col2:
                        if st.button("🗑️", key=f"del_{f['name']}", help="Delete file"):
                            result = api_delete_file(f['name'])
                            if result.get("success"):
                                st.rerun()
        else:
            st.info("No files uploaded yet")
        
        # Tables info
        tables = files_data.get("tables_loaded", [])
        if tables:
            st.divider()
            st.caption(f"**Tables:** {len(tables)}")
            for t in tables:
                st.caption(f"• {t}")
    
    # Main Chat Area
    st.markdown("## 🧠 LedgerMind")
    
    # File context indicator
    files_data = api_list_files()
    files = files_data.get("files", [])
    if files:
        file_names = [f['name'] for f in files[:3]]
        more = f" +{len(files)-3} more" if len(files) > 3 else ""
        st.caption(f"📁 Using: {', '.join(file_names)}{more}")
    else:
        st.caption("📁 No files uploaded — upload files to query your data")
    
    st.divider()
    
    # Chat History
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.chat_history:
            # Welcome message
            st.markdown("""
            **Welcome! I'm your AI CFO.** Ask me anything:
            
            - 📊 **Your Data:** "Show my sales", "What's my bank balance?"
            - 📚 **GST Rules:** "What is CGST?", "When to file GSTR-3B?"
            - ✅ **Compliance:** "Check my invoices", "Any tax issues?"
            """)
        else:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg.get("time_ms"):
                        st.caption(f"⏱️ {msg['time_ms']}ms")
    
    # Chat Input
    if prompt := st.chat_input("Ask anything..."):
        # Add user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })
        
        # Get response
        with st.spinner("Thinking..."):
            result = api_query(prompt)
        
        response = result.get("answer", "Sorry, I couldn't process that.")
        time_ms = result.get("processing_time_ms")
        
        # Add assistant message
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "time_ms": time_ms
        })
        
        st.rerun()
    
    # Clear chat button (bottom right)
    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        if st.session_state.chat_history:
            if st.button("🗑️ Clear"):
                st.session_state.chat_history = []
                st.rerun()


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    if st.session_state.logged_in:
        show_main_app()
    else:
        show_login()


if __name__ == "__main__":
    main()
