import requests
import streamlit as st
import re
from config import GOOGLE_API_KEY, GOOGLE_CX, GROQ_API_KEY, GROQ_CHAT_URL, GROQ_MODEL

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
    """Search using Groq API with better prompt"""
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Find business leads for: "{query}". For each lead, provide:
- Company name
- Brief description
- Website URL if available
- Contact information if available

Format each lead as:
[Company Name]
Description: [description]
URL: [website]
Contact: [contact info]

Separate leads with two newlines."""

        data = {
            "model": GROQ_MODEL,
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.3,
            "max_tokens": 1500
        }
        
        response = requests.post(GROQ_CHAT_URL, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"🤖 Groq search failed: {str(e)}")
        return {"choices": [{"message": {"content": ""}}]}

def extract_groq_leads(results):
    """Process Groq results into lead format"""
    leads = []
    if "choices" not in results:
        return leads
        
    content = results["choices"][0]["message"]["content"]
    
    # Split into individual leads
    lead_blocks = [block.strip() for block in content.split('\n\n') if block.strip()]
    
    for block in lead_blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        # Extract details
        title = lines[0].replace("[", "").replace("]", "")
        snippet = ""
        url = "#"
        
        for line in lines[1:]:
            if line.lower().startswith("url:"):
                url = line[4:].strip()
            else:
                snippet += line + "\n"
        
        leads.append({
            "title": title,
            "snippet": snippet.strip(),
            "url": url,
            "source": "groq"
        })
    
    return leads

def filter_leads_with_groq(prompt, leads, max_leads=15):
    """Filter and format leads using Groq"""
    if not leads:
        return "No leads found"
    
    # Prepare context
    context = "\n\n".join([
        f"Title: {lead['title']}\nDetails: {lead['snippet']}\nURL: {lead['url']}"
        for lead in leads[:max_leads]
    ])
    
    # Enhanced prompt for better formatting
    full_prompt = f"""Analyze these leads for "{prompt}" and return the most relevant ones in this format:
[Company Name]
Industry: [sector if available]
Key Details: [summary]
URL: [website]
Contact: [if available]

Separate each lead with two newlines. Here are the raw results:\n{context}"""
    
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
        response = requests.post(GROQ_CHAT_URL, headers=headers, json=data, timeout=25)
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return "No qualified leads found."
    except Exception as e:
        st.error(f"AI filtering failed: {str(e)}")
        return f"Error: {str(e)}"