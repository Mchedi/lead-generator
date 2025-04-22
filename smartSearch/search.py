import requests
import streamlit as st
import re
import time
from config import GOOGLE_API_KEY, GOOGLE_CX, GROQ_API_KEY, GROQ_SEARCH_URL, GROQ_CHAT_URL, GROQ_MODEL

def google_search(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Google search error: {str(e)}")
        return {"items": []}

def extract_google_leads(results):
    leads = []
    for item in results.get("items", []):
        leads.append({
            "title": item.get("title", "No title"),
            "snippet": item.get("snippet", "No description"),
            "url": item.get("link", "#")
        })
    return leads

def groq_search(query):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "query": query,
            "numResults": 2000,
            "temperature": 0.1
        }
        response = requests.post(GROQ_SEARCH_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Groq search error: {str(e)}")
        return {"data": []}

def extract_groq_leads(results):
    leads = []
    for item in results.get("data", []):
        leads.append({
            "title": item.get("name", "No title"),
            "snippet": item.get("additional_info", "No description"),
            "url": item.get("social_media_url", "#")
        })
    return leads

def filter_leads_with_groq(prompt, leads, max_leads=10, retries=3):
    leads = leads[:max_leads]
    context = "\n\n".join([
        f"Title: {lead['title']}\nSnippet: {lead['snippet']}\nURL: {lead['url']}" for lead in leads
    ])
    
    full_prompt = f"""You are a lead generation expert. Based on this user need:
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
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.3
    }

    for attempt in range(retries):
        try:
            response = requests.post(GROQ_CHAT_URL, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            result = response.json()
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            return "No results found."
        except Exception as e:
            if attempt == retries - 1:
                return f"Error processing leads: {str(e)}"
            time.sleep(2 ** attempt)  # Exponential backoff