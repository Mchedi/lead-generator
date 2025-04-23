import requests
import streamlit as st
import re
import time
import pandas as pd
from config import GOOGLE_API_KEY, GOOGLE_CX, GROQ_API_KEY, GROQ_SEARCH_URL, GROQ_CHAT_URL, GROQ_MODEL
from ml_filter import LeadScorer

def google_search(query):
    """Enhanced Google search with better error handling and timeout"""
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=10"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"🔍 Google search failed: {str(e)}")
        return {"items": []}
    except Exception as e:
        st.error(f"Unexpected error in Google search: {str(e)}")
        return {"items": []}

def extract_google_leads(results):
    """Enhanced lead extraction with data validation"""
    leads = []
    for item in results.get("items", []):
        try:
            # Clean the snippet text
            snippet = item.get("snippet", "No description")
            snippet = re.sub(r'\s+', ' ', snippet)  # Remove extra whitespace
            snippet = re.sub(r'\[.*?\]', '', snippet)  # Remove brackets
            
            leads.append({
                "title": item.get("title", "No title").strip(),
                "snippet": snippet,
                "url": item.get("link", "#"),
                "source": "google"
            })
        except Exception as e:
            st.warning(f"Couldn't process one search result: {str(e)}")
    return leads

def groq_search(query):
    """Alternative Groq implementation using chat completion"""
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": GROQ_MODEL,
            "messages": [{
                "role": "user",
                "content": f"Find business opportunities about: {query}. Return as structured data."
            }],
            "temperature": 0.2,
            "max_tokens": 1000
        }
        response = requests.post(GROQ_CHAT_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        
        # Process the response
        result = response.json()
        if "choices" in result:
            content = result["choices"][0]["message"]["content"]
            return {
                "data": [{
                    "name": content[:50] + "...",
                    "additional_info": content,
                    "social_media_url": "#",
                    "date": "2023-01-01",
                    "location": "Unknown"
                }]
            }
        return {"data": []}
    except Exception as e:
        st.error(f"🤖 Groq search failed: {str(e)}")
        return {"data": []}

def extract_groq_leads(results):
    """Process Groq results"""
    leads = []
    for item in results.get("data", []):
        leads.append({
            "title": item.get("name", "No title").strip(),
            "snippet": item.get("additional_info", "No description"),
            "url": item.get("social_media_url", "#"),
            "source": "groq",
            "date": item.get("date", ""),
            "location": item.get("location", "")
        })
    return leads

def filter_leads_with_groq(prompt, leads, max_leads=15):
    """ML-enhanced lead filtering with structured output"""
    leads = leads[:max_leads]
    
    # Prepare context
    context = "\n\n".join([
        f"Title: {lead['title']}\nSnippet: {lead['snippet']}\nURL: {lead['url']}"
        for lead in leads
    ])
    
    # Enhanced prompt
    full_prompt = f"""Analyze these leads for "{prompt}". For each, provide:
1. [Company/Contact]
2. Industry: [sector]
3. Need: [requirement]
4. URL: [source]
Separate leads with 2 newlines. Results:\n{context}"""
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.4,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(GROQ_CHAT_URL, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return "No qualified leads found."
    except Exception as e:
        st.error(f"AI filtering failed: {str(e)}")
        return f"Error: {str(e)}"

def analyze_lead_trends(leads):
    """Generate insights about lead patterns"""
    if not leads:
        return "No leads available for analysis"
    
    try:
        df = pd.DataFrame(leads)
        return f"Found {len(df)} leads across {df['source'].nunique()} sources."
    except Exception as e:
        return f"Analysis error: {str(e)}"