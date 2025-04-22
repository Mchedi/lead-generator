import json
import os
from datetime import datetime
import streamlit as st
import time
from config import MEMORY_FILE, MAX_MESSAGES

def load_memory():
    """Load conversation history from file"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {}
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
        st.session_state.user_id = str(hash(st.experimental_user.id)) if hasattr(st, 'experimental_user') and st.experimental_user else str(hash(time.time()))
    return st.session_state.user_id

def manage_memory(messages, max_messages=MAX_MESSAGES):
    """Manage conversation history length"""
    if len(messages) > max_messages:
        return [messages[0]] + messages[-(max_messages-1):]
    return messages