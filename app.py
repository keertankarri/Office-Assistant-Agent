__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from database import init_db, fetch_table_data, save_table_data
from agent import handle_user_request
from ocr_engine import process_uploaded_image

load_dotenv()
init_db()

st.set_page_config(page_title="TechNova Office Assistant", layout="wide")
st.title("TechNova Enterprise Agentic Assistant")

# Sidebar - Employee Context & OCR Ingestion
st.sidebar.header("Employee Context")
emp_id = st.sidebar.text_input("Active Employee ID", value="EMP101")

st.sidebar.subheader("OCR Document Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Receipt / Certificate", type=["png", "jpg", "jpeg"])

ocr_text = None
if uploaded_file:
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    ocr_text = process_uploaded_image(temp_path)
    st.sidebar.success("OCR Processing Complete")
    st.sidebar.text_area("Extracted OCR Text", ocr_text, height=120)
    os.remove(temp_path)

# Main Application Tabs
tab_chat, tab_db, tab_analytics = st.tabs([
    "💬 Assistant Chat", 
    "🗄️ SQLite Database Viewer", 
    "📊 Analytics Dashboard"
])

# Tab 1: Assistant Chat
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a policy question, view records, or apply for leave..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processing request..."):
                response = handle_user_request(prompt, emp_id=emp_id, ocr_text=ocr_text)
                st.markdown(response)
                
        st.session_state.messages.append({"role": "assistant", "content": response})

# Tab 2: Database Viewer
with tab_db:
    st.subheader("Manage Local SQLite Database")
    selected_table = st.selectbox("Select Table to View/Edit", ["leave_balances", "employees", "analytics_logs"])
    
    df = fetch_table_data(selected_table)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("Save Changes to Database"):
        save_table_data(selected_table, edited_df)
        st.success(f"Changes saved successfully to table '{selected_table}'!")

# Tab 3: Analytics Dashboard
with tab_analytics:
    st.subheader("Agent Performance & Usage Metrics")
    
    df_logs = fetch_table_data("analytics_logs")
    df_leaves = fetch_table_data("leave_balances")
    
    if df_logs.empty:
        st.info("No query logs recorded yet. Ask a question in the chat tab to generate telemetry!")
    else:
        # High-Level Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Queries Handled", len(df_logs))
        m2.metric("Most Active User", df_logs["emp_id"].mode()[0] if not df_logs.empty else "N/A")
        m3.metric("Top Intent Category", df_logs["category"].mode()[0] if not df_logs.empty else "N/A")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Query Volume by Intent Category**")
            st.bar_chart(df_logs["category"].value_counts())
            
        with col2:
            st.markdown("**Current Leave Balances Overview**")
            if not df_leaves.empty:
                st.bar_chart(df_leaves.set_index("emp_id")[["casual_leave", "earned_leave", "sick_leave"]])

        st.markdown("**Recent System Execution Audit Logs**")
        st.dataframe(df_logs.sort_values(by="id", ascending=False), use_container_width=True)