# LedgerMind Streamlit UI
"""
Internal tool for testing and debugging the LLM.

NOT for customers - this is OUR tool to test.

Run:
    streamlit run streamlit/app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.customer import CustomerManager, CustomerContext
from orchestration.workflow import AgentWorkflow
from llm.client import LLMClient


# =============================================================================
# Page Config
# =============================================================================

st.set_page_config(
    page_title="LedgerMind Admin",
    page_icon="🧠",
    layout="wide"
)


# =============================================================================
# Session State
# =============================================================================

if "customer" not in st.session_state:
    st.session_state.customer = None
if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# =============================================================================
# Sidebar - Customer Selection
# =============================================================================

st.sidebar.title("🧠 LedgerMind Admin")
st.sidebar.caption("Internal testing tool")

# LLM Status
llm = LLMClient()
if llm.is_available():
    st.sidebar.success("✅ LLM Online")
else:
    st.sidebar.error("❌ LLM Offline - Start Ollama")

st.sidebar.divider()

# Customer selection
manager = CustomerManager()
customers = manager.list_customers()

customer_options = ["Select customer..."] + [c["customer_id"] for c in customers]
selected = st.sidebar.selectbox("Customer", customer_options)

if selected != "Select customer...":
    if st.session_state.customer != selected:
        st.session_state.customer = selected
        ctx = manager.get_customer(selected)
        ctx.ensure_exists()
        st.session_state.workflow = AgentWorkflow(customer=ctx)
        st.session_state.chat_history = []
        st.rerun()

# New customer
with st.sidebar.expander("➕ New Customer"):
    new_id = st.text_input("Customer ID", placeholder="company_name")
    if st.button("Create") and new_id:
        try:
            ctx = manager.create_customer(new_id)
            st.success(f"Created: {new_id}")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

st.sidebar.divider()

# File upload (if customer selected)
if st.session_state.customer:
    st.sidebar.subheader("📁 Upload Data")
    uploaded = st.sidebar.file_uploader(
        "Excel/CSV files",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True
    )
    
    if uploaded:
        ctx = manager.get_customer(st.session_state.customer)
        for file in uploaded:
            save_path = ctx.data_dir / file.name
            save_path.write_bytes(file.read())
        st.sidebar.success(f"Uploaded {len(uploaded)} file(s)")
        
        # Trigger reload
        if st.sidebar.button("🔄 Load into DB"):
            st.session_state.workflow = AgentWorkflow(customer=ctx)
            st.rerun()


# =============================================================================
# Main Area - Chat Interface
# =============================================================================

st.title("🧠 LedgerMind")

if not st.session_state.customer:
    st.info("👈 Select a customer from the sidebar to start")
    st.stop()

st.caption(f"Testing as: **{st.session_state.customer}**")

# Chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask anything..."):
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if st.session_state.workflow:
                response = st.session_state.workflow.run(prompt)
            else:
                response = "❌ No workflow initialized"
        
        st.markdown(response)
    
    # Add assistant message
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# Clear chat button
if st.session_state.chat_history:
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

