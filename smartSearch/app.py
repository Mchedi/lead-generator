import streamlit as st
from memory import load_memory, save_memory, get_user_id, manage_memory
from search import google_search, extract_google_leads, groq_search, extract_groq_leads, filter_leads_with_groq
from chathun import chat_with_groq
from config import MEMORY_FILE
from config import GOOGLE_API_KEY, GOOGLE_CX, GROQ_API_KEY, MEMORY_FILE
import json
import re

def main():
    st.set_page_config(page_title="Lead Extractor + Chatbot", layout="wide")
    st.title("🔍 AI-Powered Lead Extractor with Chat Assistant")

    # Initialize memory
    user_id = get_user_id()
    memory = load_memory()

    col1, col2 = st.columns([2, 1])  # Left: Main app | Right: Chatbot

    # ------------------- Lead Search Section -------------------
    with col1:
        st.header("Lead Search")
        with st.sidebar:
            st.header("🔐 API Keys")
            st.text_input("Google API Key", value=GOOGLE_API_KEY, type="password", key="google_key")
            st.text_input("Google CX", value=GOOGLE_CX, key="cx")
            st.text_input("Groq API Key", value=GROQ_API_KEY, type="password", key="groq_key")
            use_groq_search = st.checkbox("Include Groq Search Results", value=False)

            # Memory management
            st.header("🧠 Memory Settings")
            if st.button("Clear My Chat History"):
                if user_id in memory:
                    del memory[user_id]
                    with open(MEMORY_FILE, 'w') as f:
                        json.dump(memory, f)
                    st.session_state.messages = [
                        {"role": "system", "content": "You are a helpful business assistant for lead generation."},
                        {"role": "assistant", "content": "Hello! How can I help you with lead generation today?"}
                    ]
                    st.rerun()

        user_query = st.text_input("What type of lead are you looking for?", placeholder="e.g. Companies needing IoT consulting")

        if st.button("Search Leads") and user_query:
            st.write("⏳ Searching and filtering leads...")

            with st.spinner("Searching Google..."):
                google_raw = google_search(user_query)
                google_leads = extract_google_leads(google_raw)

            groq_leads = []
            if use_groq_search:
                with st.spinner("Searching Groq..."):
                    groq_raw = groq_search(user_query)
                    groq_leads = extract_groq_leads(groq_raw)

            all_leads = google_leads + groq_leads

            if not all_leads:
                st.warning("No leads found.")
                return

            with st.spinner("🤖 Filtering with AI..."):
                filtered = filter_leads_with_groq(user_query, all_leads)

            st.subheader("🌟 Filtered Leads")

            # Check if the response looks like a list/markdown
            if "- " in filtered or "* " in filtered or "\n" in filtered:
                # Process as markdown
                st.markdown(filtered)
            else:
                # Create a more structured display
                with st.expander("View AI Analysis", expanded=True):
                    st.markdown("""
                    <style>
                        .lead-card {
                            border: 1px solid #e0e0e0;
                            border-radius: 8px;
                            padding: 15px;
                            margin-bottom: 15px;
                            background-color: #f9f9f9;
                        }
                        .lead-title {
                            font-weight: bold;
                            color: #2c3e50;
                            font-size: 1.1em;
                            margin-bottom: 5px;
                        }
                        .lead-snippet {
                            color: #34495e;
                            margin-bottom: 8px;
                        }
                        .lead-url {
                            color: #3498db;
                            font-size: 0.9em;
                        }
                        .lead-score {
                            display: inline-block;
                            background-color: #e3f2fd;
                            padding: 2px 8px;
                            border-radius: 12px;
                            font-size: 0.8em;
                            margin-right: 8px;
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    leads = filtered.split('\n\n')

                    for lead in leads:
                        if not lead.strip():
                            continue

                        url_match = re.search(r'(https?://\S+)', lead)
                        url = url_match.group(1) if url_match else "#"

                        st.markdown(f"""
                        <div class="lead-card">
                            <div class="lead-title">{lead.split('\n')[0] if '\n' in lead else lead}</div>
                            <div class="lead-snippet">{'<br>'.join(lead.split('\n')[1:]) if '\n' in lead else 'No additional details'}</div>
                            <div class="lead-url"><a href="{url}" target="_blank">View Source</a></div>
                        </div>
                        """, unsafe_allow_html=True)

            st.download_button(
                label="📅 Download Leads",
                data=filtered,
                file_name=f"filtered_leads_{user_query[:20]}.txt",
                mime="text/plain"
            )

            st.subheader("🌐 Raw Search Results")
            for lead in all_leads:
                st.markdown(f"**{lead['title']}**")
                st.markdown(lead['snippet'])
                st.markdown(f"[🔗 Link]({lead['url']})")
                st.markdown("---")

    # ------------------- Chatbot Section -------------------
    with col2:
        st.header("💬 Chat Assistant")

        if "messages" not in st.session_state:
            if user_id in memory and "conversation" in memory[user_id]:
                st.session_state.messages = memory[user_id]["conversation"]
                st.info("Loaded previous conversation")
            else:
                st.session_state.messages = [
                    {"role": "system", "content": "You are a helpful business assistant for lead generation."},
                    {"role": "assistant", "content": "Hello! How can I help you with lead generation today?"}
                ]

        for message in st.session_state.messages[1:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask me anything about lead gen or strategy..."):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_with_groq(st.session_state.messages)

                    if not response or "sorry" in response.lower():
                        response = "I couldn't process that request. Please try again or rephrase your question."

                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

            st.session_state.messages = manage_memory(st.session_state.messages)
            save_memory(user_id, st.session_state.messages)

if __name__ == "__main__":
    main()
