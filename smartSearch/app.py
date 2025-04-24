import streamlit as st
from memory import load_memory, save_memory, get_user_id, manage_memory
from search import google_search, extract_google_leads, groq_search, extract_groq_leads, filter_leads_with_groq
from chathun import chat_with_groq
from config import GOOGLE_API_KEY, GOOGLE_CX, GROQ_API_KEY, MEMORY_FILE
from Lead_display import display_leads
import json
import re

def main():
    st.set_page_config(page_title="Lead Intelligence Pro", layout="wide")
    st.title("🚀 AI-Powered Lead Intelligence Platform")

    # Initialize session state
    if 'current_leads' not in st.session_state:
        st.session_state.current_leads = []
    if 'search_executed' not in st.session_state:
        st.session_state.search_executed = False

    # Initialize memory
    user_id = get_user_id()
    memory = load_memory()

    col1, col2 = st.columns([2, 1])

    # Lead Discovery Column
    with col1:
        st.header("🔍 Lead Discovery Engine")
        
        # Search configuration
        with st.sidebar:
            st.header("⚙️ Configuration")
            with st.expander("API Settings"):
                google_key = st.text_input("Google API Key", value=GOOGLE_API_KEY, type="password")
                google_cx = st.text_input("Google CX", value=GOOGLE_CX)
                groq_key = st.text_input("Groq API Key", value=GROQ_API_KEY, type="password")

        # Search interface
        user_query = st.text_input(
            "Describe your ideal lead opportunity:",
            placeholder="e.g. Mobile app development companies in Berlin"
        )
        
        if st.button("🚀 Find Leads", type="primary"):
            if user_query:
                with st.status("Searching for leads...", expanded=True):
                    # Execute searches
                    st.write("🔎 Querying Groq...")
                    groq_results = groq_search(user_query)
                    groq_leads = extract_groq_leads(groq_results)
                    
                    st.write("🌐 Searching Google...")
                    google_results = google_search(user_query)
                    google_leads = extract_google_leads(google_results)
                    
                    all_leads = groq_leads + google_leads
                    
                    if not all_leads:
                        st.warning("No leads found. Try different search terms.")
                        return
                    
                    # Process and store leads
                    processed_leads = []
                    for lead in all_leads:
                        processed = {
                            'name': lead.get('title', 'Unknown Company'),
                            'details': lead.get('snippet', 'No details available'),
                            'url': lead.get('url', None)
                        }
                        if 'industry' in lead:
                            processed['industry'] = lead['industry']
                        processed_leads.append(processed)
                    
                    st.session_state.current_leads = processed_leads
                    st.session_state.search_executed = True
                    st.success(f"Found {len(processed_leads)} leads!")
            
        # Display results if search was executed
        if st.session_state.search_executed:
            st.subheader("💎 Lead Results")
            display_leads(st.session_state.current_leads, user_query)

    # AI Analyst Column
    with col2:
        st.header("💬 AI Strategy Analyst")
        
        # Initialize chat
        if "messages" not in st.session_state:
            if user_id in memory and "conversation" in memory[user_id]:
                st.session_state.messages = memory[user_id]["conversation"]
            else:
                st.session_state.messages = [
                    {"role": "assistant", "content": "I'm ready to analyze lead opportunities. What shall we examine today?"}
                ]
        
        # Display chat history
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about lead strategy..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            with st.chat_message("assistant"):
                response = chat_with_groq(st.session_state.messages)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Save conversation
            save_memory(user_id, st.session_state.messages)

if __name__ == "__main__":
    main()