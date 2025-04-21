import requests
import streamlit as st
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
GOOGLE_API_KEY = "AIzaSyBxfzMOlpuR1QVBym_LeAayEqAfvn8ZcWs"
GOOGLE_CX = "94e638b8528184bdf"
GROQ_API_KEY = "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"
        
        # API endpoints
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"
TEMPERATURE = 0.3
MAX_TOKENS = 4000
# ------------------------
# CONFIGURATION
# ------------------------
class Config:
    """Centralized configuration for the lead scraper"""
    def __init__(self):
        # API keys (should be stored securely in production)
        
        # Search parameters
        self.B2B_SOURCES = [
            "smtnet.com",
            "alibaba.com",
            "globalsmt.net",
            "pcbmart.com"
        ]
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # AI parameters
       

config = Config()

# ------------------------
# SEARCH MODULE
# ------------------------
class LeadScraper:
    """Handles all search and scraping operations"""
    
    @staticmethod
    def google_search(query):
        """Enhanced Google search with B2B focus"""
        b2b_query = f'{query} ("wanted" OR "looking for" OR "contact supplier") {" OR ".join([f"site:{site}" for site in config.B2B_SOURCES])}'
        url = f"https://www.googleapis.com/customsearch/v1?q={b2b_query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=10"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Google search failed: {str(e)}")
            return None
    
    @staticmethod
    def scrape_website(url):
        """Direct website scraping with BeautifulSoup"""
        headers = {"User-Agent": config.USER_AGENT}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract potential leads - this would be customized per target site
            leads = []
            for post in soup.select(".post, .listing, .result"):
                lead = {
                    "title": post.select_one("h1, h2, h3, .title").get_text(strip=True) if post.select_one("h1, h2, h3, .title") else "No title",
                    "content": post.get_text(" ", strip=True),
                    "url": url,
                    "source": "Direct Scrape",
                    "timestamp": datetime.now().isoformat()
                }
                leads.append(lead)
            return leads
        except Exception as e:
            st.error(f"Scraping failed for {url}: {str(e)}")
            return []

# ------------------------
# AI PROCESSING MODULE
# ------------------------
class AIProcessor:
    """Handles all AI-related processing"""
    
    @staticmethod
    def generate_extraction_prompt(query):
        """Generate prompt for initial lead extraction"""
        return [
            {
                "role": "system",
                "content": """You are a professional B2B lead extraction AI. Extract structured information from raw content.
                Return JSON format with these fields for each lead:
                - company: string (company name)
                - contact: string (email/phone/contact person)
                - requirements: string (what they're looking for)
                - source_url: string (original URL)
                - confidence: "High"/"Medium"/"Low" (your confidence in this lead)
                """
            },
            {
                "role": "user",
                "content": f"""Extract leads for companies looking to purchase: {query}
                Focus on posts showing buying intent (e.g., "want to buy", "looking for supplier").
                Exclude sellers, academic requests, and irrelevant content."""
            }
        ]
    
    @staticmethod
    def generate_refinement_prompt(refinement_criteria, existing_leads):
        """Generate prompt for refining existing leads"""
        return [
            {
                "role": "system",
                "content": """You are a lead refinement AI. Filter and enhance existing leads based on new criteria.
                Maintain the original JSON structure while adding:
                - location: if geographic filter applies
                - urgency: if timeframe mentioned
                - quantity: if specified
                """
            },
            {
                "role": "assistant",
                "content": f"Current leads: {json.dumps(existing_leads)}"
            },
            {
                "role": "user",
                "content": f"""Refine leads based on: {refinement_criteria}
                Keep only leads matching these criteria while preserving all original valid information."""
            }
        ]
    
    @staticmethod
    def process_with_ai(messages):
        """Send prompt to Groq API and handle response"""
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": messages,
            "model": GROQ_MODEL,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(GROQ_CHAT_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
            # Handle JSON embedded in text
            if isinstance(content, str):
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json_match.group()
            return content
            
        except Exception as e:
            st.error(f"AI processing failed: {str(e)}")
            if 'response' in locals():
                st.error(f"API response: {response.text}")
            return None

# ------------------------
# DATA PROCESSING MODULE
# ------------------------
class DataProcessor:
    """Handles data transformation and validation"""
    
    @staticmethod
    def parse_ai_response(response):
        """Parse and validate AI response"""
        if not response:
            return None
            
        try:
            data = json.loads(response)
            if isinstance(data, dict):
                return [data]  # Convert single object to list
            return data
        except json.JSONDecodeError:
            st.error("Failed to parse AI response")
            return None
    
    @staticmethod
  
    @staticmethod
    def prepare_for_display(leads):
        """Convert leads to display-friendly format"""
        if not leads:
            return pd.DataFrame()
            
        display_data = []
        for lead in leads:
            display_data.append({
                "Company": lead.get("company", "Unknown"),
                "Contact": lead.get("contact", ""),
                "Requirements": lead.get("requirements", ""),
                "Location": lead.get("location", ""),
                "Urgency": lead.get("urgency", ""),
                "Quantity": lead.get("quantity", ""),
                "Confidence": lead.get("confidence", "Low"),
                "Source": lead.get("source_url", "")
            })
        return pd.DataFrame(display_data)

# ------------------------
# STREAMLIT UI
# ------------------------
def main():
    st.set_page_config(
        page_title="AI Lead Scraper Pro",
        layout="wide",
        page_icon="🔍"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .lead-card {
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
        border-radius: 0.25rem;
    }
    .confidence-high {
        color: #4CAF50;
        font-weight: bold;
    }
    .confidence-medium {
        color: #FFC107;
        font-weight: bold;
    }
    .confidence-low {
        color: #F44336;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔍 AI-Powered Lead Scraper")
    st.caption("Extract and qualify B2B leads automatically")
    
    # Initialize session state
    if 'leads' not in st.session_state:
        st.session_state.leads = []
    if 'filtered_leads' not in st.session_state:
        st.session_state.filtered_leads = []
    
    # Main search interface
    with st.expander("🔎 Search Parameters", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            search_query = st.text_input(
                "What are you looking for?",
                placeholder="e.g., FUJI AIMEX-II machines",
                help="Be specific about products/services"
            )
        with col2:
            search_method = st.radio(
                "Search method:",
                ["Google Search API", "Direct Website Scrape"],
                horizontal=True
            )
            
        if search_method == "Direct Website Scrape":
            target_url = st.text_input(
                "Enter URL to scrape:",
                placeholder="https://example.com/listings"
            )
    
    # Search execution
    if st.button("Search for Leads", type="primary"):
        with st.spinner("Searching..."):
            raw_leads = []
            
            if search_method == "Google Search API":
                results = LeadScraper.google_search(search_query)
                if results and 'items' in results:
                    for item in results['items']:
                        raw_leads.append({
                            "title": item.get("title", ""),
                            "content": item.get("snippet", ""),
                            "url": item.get("link", ""),
                            "source": "Google",
                            "timestamp": datetime.now().isoformat()
                        })
            else:
                if target_url:
                    raw_leads = LeadScraper.scrape_website(target_url)
            
            if not raw_leads:
                st.warning("No raw leads found. Try different search terms.")
                st.stop()
            
            # AI Processing
            ai_messages = AIProcessor.generate_extraction_prompt(search_query)
            ai_messages.append({
                "role": "user",
                "content": f"Raw leads to process: {json.dumps(raw_leads)}"
            })
            
            ai_response = AIProcessor.process_with_ai(ai_messages)
            parsed_leads = DataProcessor.parse_ai_response(ai_response)
            
            if parsed_leads:
                st.session_state.leads = parsed_leads
                st.session_state.filtered_leads = parsed_leads
                st.success(f"Found {len(parsed_leads)} potential leads!")
            else:
                st.error("Failed to extract leads from results")

    # Display and filter results
    if st.session_state.leads:
        with st.expander("🎯 Lead Results", expanded=True):
           
            # Apply filter
                
            
            
            # Display filtered results
            if st.session_state.filtered_leads:
                st.write(f"Showing {len(st.session_state.filtered_leads)}/{len(st.session_state.leads)} leads")
                
                # Tabbed view - Table and Cards
                tab1, tab2 = st.tabs(["Data Table", "Lead Cards"])
                
                with tab1:
                    df = DataProcessor.prepare_for_display(st.session_state.filtered_leads)
                    st.dataframe(df, use_container_width=True)
                    
                    # Export options
                    st.download_button(
                        label="Export as CSV",
                        data=df.to_csv(index=False),
                        file_name="leads.csv",
                        mime="text/csv"
                    )
                
                with tab2:
                    for lead in st.session_state.filtered_leads:
                        confidence_class = f"confidence-lead.get('confidence', 'low').lower()"
                        st.markdown(f"""
                        <div class="lead-card">
                            <h3>{lead.get('company', 'Unknown Company')}</h3>
                            <p><strong>Looking for:</strong> {lead.get('requirements', 'Not specified')}</p>
                            <div style="display: flex; gap: 1rem;">
                                <div><strong>Contact:</strong> {lead.get('contact', 'Not provided')}</div>
                                <div><strong>Location:</strong> {lead.get('location', 'Not specified')}</div>
                            </div>
                            <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
                                <div><strong>Urgency:</strong> {lead.get('urgency', 'Not specified')}</div>
                                <div><strong>Quantity:</strong> {lead.get('quantity', 'N/A')}</div>
                            </div>
                            <p style="margin-top: 0.5rem;">
                                <span class="{confidence_class}">Confidence: {lead.get('confidence', 'Low')}</span> | 
                                <a href="{lead.get('source_url', '#')}" target="_blank">Source</a>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("No leads meet the current confidence filter")
    
        # Refinement section
        with st.expander("✨ Refine Leads", expanded=False):
            refinement_query = st.text_input(
                "Further refine leads by:",
                placeholder="e.g., 'Companies in Europe needing 5+ units'"
            )
            
            if st.button("Apply Refinement"):
                with st.spinner("Refining leads..."):
                    if not st.session_state.filtered_leads:
                        st.warning("No leads to refine")
                        st.stop()
                    
                    ai_messages = AIProcessor.generate_refinement_prompt(
                        refinement_query,
                        st.session_state.filtered_leads
                    )
                    
                    ai_response = AIProcessor.process_with_ai(ai_messages)
                    refined_leads = DataProcessor.parse_ai_response(ai_response)
                    
                    if refined_leads:
                        st.session_state.leads = refined_leads
                        st.session_state.filtered_leads = refined_leads
                        st.success(f"Refined to {len(refined_leads)} leads!")
                    else:
                        st.error("Refinement failed")

if __name__ == "__main__":
    main()