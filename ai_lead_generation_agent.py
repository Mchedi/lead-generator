import requests
import streamlit as st
import re
import time
import json
import os
from datetime import datetime

# ------------------------
# CONFIG
# ------------------------
GOOGLE_API_KEY = "AIzaSyBxfzMOlpuR1QVBym_LeAayEqAfvn8ZcWs"
GOOGLE_CX = "94e638b8528184bdf"
GROQ_API_KEY = "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"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_SEARCH_URL = "https://api.groq.com/v1/search"
GROQ_MODEL = "mixtral-8x7b-32768"
MEMORY_FILE = "chat_memory.json"  # File to store conversation history

# ------------------------
# MEMORY FUNCTIONS
# ------------------------
def load_memory():
    """Load conversation history from file"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading memory: {e}")
    return {}

def save_memory(user_id, conversation):
    """Save conversation history to file"""
    try:
        memory = load_memory()
        memory[user_id] = {
            "conversation": conversation,
            "last_updated": datetime.now().isoformat()
        }
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        st.error(f"Error saving memory: {e}")

def get_user_id():
    """Generate a unique user identifier for session"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(hash(st.experimental_user.id)) if st.experimental_user else str(hash(time.time()))
    return st.session_state.user_id

def manage_memory(messages, max_messages=20):
    """Manage conversation history length"""
    # Keep system message and trim oldest user/assistant pairs if needed
    if len(messages) > max_messages:
        return [messages[0]] + messages[-(max_messages-1):]
    return messages

# ------------------------
# SEARCH FUNCTIONS
# ------------------------
def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
    return requests.get(url).json()

def extract_google_leads(results):
    leads = []
    for item in results.get("items", []):
        leads.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "url": item.get("link")
        })
    return leads

def groq_search(query):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "numResults": 2000,
        "temperature": 0.1
    }
    return requests.post(GROQ_SEARCH_URL, headers=headers, json=data).json()

def extract_groq_leads(results):
    leads = []
    for item in results.get("data", []):
        leads.append({
            "title": item.get("name", "N/A"),
            "snippet": item.get("additional_info", ""),
            "url": item.get("social_media_url", "N/A")
        })
    return leads

# ------------------------
# LEAD FILTERING FUNCTION
# ------------------------
def filter_leads_with_groq(prompt, leads, max_leads=10, retries=3):
    leads = leads[:max_leads]
    context = "\n\n".join([
        f"Title: {lead['title']}\nSnippet: {lead['snippet']}\nURL: {lead['url']}" for lead in leads
    ])
    full_prompt = f"""
You are a lead generation expert. Based on this user need:
"{prompt}"

Filter the following search results and return only leads that look like genuine business opportunities.
Focus on people wanting to buy products or post freelance job requests (not student projects).
Also highlight if someone has worked with or hired for this topic before.

Results:
{context}
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": full_prompt}]
    }

    for _ in range(retries):
        response = requests.post(GROQ_CHAT_URL, headers=headers, json=data)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        elif "error" in result and "rate_limit" in result["error"].get("code", ""):
            wait_time = float(re.search(r'(\d+\.\d+)s', result["error"]["message"]).group(1))
            time.sleep(wait_time + 1)
        else:
            return f"Error extracting leads: {result.get('error', 'Unknown error')}\n\nRaw: {result}"
    return "❌ Failed after retries due to rate limit or unknown error."

# ------------------------
# GROQ CHATBOT HANDLER
# ------------------------
def chat_with_groq(messages):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": messages
    }
    response = requests.post(GROQ_CHAT_URL, headers=headers, json=data)
    result = response.json()
    return result["choices"][0]["message"]["content"] if "choices" in result else "Sorry, I couldn't process that."

# ------------------------
# STREAMLIT APP
# ------------------------
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
            
            # Memory management options
            st.header("🧠 Memory Settings")
            if st.button("Clear My Chat History"):
                if user_id in memory:
                    del memory[user_id]
                    with open(MEMORY_FILE, 'w') as f:
                        json.dump(memory, f)
                    st.session_state.chat_history = [{"role": "system", "content": "You are a helpful business assistant for lead generation."}]
                    st.rerun()

        user_query = st.text_input("What type of lead are you looking for?", placeholder="e.g. Companies needing IoT consulting")

        if st.button("Search Leads") and user_query:
            st.write("⏳ Searching and filtering leads...")
            google_raw = google_search(user_query)
            google_leads = extract_google_leads(google_raw)
            groq_leads = extract_groq_leads(groq_search(user_query)) if use_groq_search else []
            all_leads = google_leads + groq_leads

            if not all_leads:
                st.warning("No leads found.")
                return

            with st.spinner("🤖 Filtering with Groq..."):
                filtered = filter_leads_with_groq(user_query, all_leads)

            st.subheader("🎯 Filtered Leads (LLM Output)")
            st.text_area("Results", filtered, height=400)

            st.subheader("🌐 Raw Search Results")
            for lead in all_leads:
                st.markdown(f"**{lead['title']}**")
                st.markdown(lead['snippet'])
                st.markdown(f"[🔗 Link]({lead['url']})")
                st.markdown("---")

    # ------------------- Improved Chatbot Section -------------------
    with col2:
        st.header("💬 Chat Assistant")

        # Initialize chat history from memory or create new
        if "chat_history" not in st.session_state:
            if user_id in memory:
                st.session_state.chat_history = memory[user_id]["conversation"]
                st.info("Loaded previous conversation from memory")
            else:
                st.session_state.chat_history = [
                    {"role": "system", "content": "You are a helpful business assistant for lead generation. You remember previous conversations to provide better assistance."}
                ]

        # Create a container for chat messages
        chat_container = st.container()
        
        # Display chat history in the container
        with chat_container:
            for msg in st.session_state.chat_history[1:]:  # skip system message
                st.chat_message(msg["role"]).write(msg["content"])

        # Place the input box below the messages
        user_input = st.chat_input("Ask me anything about lead gen or strategy...", key="chat_input")
        
        if user_input:
            # Add user message to history and display it
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with chat_container:
                st.chat_message("user").write(user_input)

            with st.spinner("Thinking..."):
                reply = chat_with_groq(st.session_state.chat_history)
            
            # Add assistant reply to history and display it
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            with chat_container:
                st.chat_message("assistant").write(reply)
            
            # Manage memory length and save
            st.session_state.chat_history = manage_memory(st.session_state.chat_history)
            save_memory(user_id, st.session_state.chat_history)

if __name__ == "__main__":
    main()