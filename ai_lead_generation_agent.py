import requests
import streamlit as st

# ------------------------
# CONFIG
# ------------------------
GOOGLE_API_KEY = "AIzaSyBxfzMOlpuR1QVBym_LeAayEqAfvn8ZcWs"
GOOGLE_CX = "94e638b8528184bdf"

GROQ_API_KEY = "gffrfsk_MaN1hRKHkJ3eYxeOExcdWGdyb3FYRLVQafWTlk8Tt1vIOro6LMdp"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"  # For GPT-style chat
GROQ_SEARCH_URL = "https://api.groq.com/v1/search"  # If you use Groq's custom search (optional)

GROQ_MODEL = "compound-beta"

# ------------------------
# SEARCH: Google
# ------------------------
def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
    response = requests.get(url)
    return response.json()

def extract_google_leads(results):
    leads = []
    for item in results.get("items", []):
        leads.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "url": item.get("link")
        })
    return leads

# ------------------------
# SEARCH: Groq (Optional)
# ------------------------
def groq_search(query):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "numResults": 2000,
        "tempeature":0.1
    }
    response = requests.post(GROQ_SEARCH_URL, headers=headers, json=data)
    return response.json()

def extract_groq_leads(results):
    leads = []
    for item in results.get("data", []):  # This depends on Groq's structure
        leads.append({
            "title": item.get("name", "N/A"),
            "snippet": item.get("additional_info", ""),
            "url": item.get("social_media_url", "N/A")
        })
    return leads

# ------------------------
# GPT-Like Filtering via Groq Chat API
# ------------------------
def filter_leads_with_groq(prompt, leads):
    context = "\n\n".join([
        f"Title: {lead['title']}\nSnippet: {lead['snippet']}\nURL: {lead['url']}" for lead in leads
    ])
    
    full_prompt = f"""
You are a lead generation expert and You're a helpful AI assistant.. Based on this user need:
"{prompt}"

Filter the following search results and return only leads that look like genuine business opportunities 
look for post  where people want to buy the prodcut 
 You will assist users with their queries about  potential customer (Lead) that are interested  in {prompt} project, by project i mean free lance opportunity, not student project .
find also people that have worked with it 
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
        #"temperature": 0.3
    }

    response = requests.post(GROQ_CHAT_URL, headers=headers, json=data)
    result = response.json()
    
    try:
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error extracting leads: {e}\n\nRaw: {result}"

# ------------------------
# Streamlit UI
# ------------------------
def main():
    st.set_page_config(page_title="🔍 Lead Extractor with Groq + Google", layout="centered")
    st.title("🔍 AI-Powered Lead Extractor (Groq + Google Search)")
    st.write("Enter a business intent, and let the app find relevant leads from the web.")

    with st.sidebar:
        st.header("🔐 API Keys")
        google_api = st.text_input("Google API Key", value=GOOGLE_API_KEY, type="password")
        google_cx = st.text_input("Google CX", value=GOOGLE_CX)
        groq_api = st.text_input("Groq API Key", value=GROQ_API_KEY, type="password")
        use_groq_search = st.checkbox("Include Groq Search Results", value=False)

    user_query = st.text_input("What type of lead are you looking for?", 
                               placeholder="e.g. Companies requesting PCB manufacturing services")

    if st.button("Search Leads") and user_query:
        st.write("⏳ Searching and filtering leads...")

       

        # Search Google
        google_raw = google_search(user_query)
        google_leads = extract_google_leads(google_raw)

        # Optional Groq search
        groq_leads = []
        if use_groq_search:
            groq_raw = groq_search(user_query)
            groq_leads = extract_groq_leads(groq_raw)

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

if __name__ == "__main__":
    main()