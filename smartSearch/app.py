import streamlit as st
import pandas as pd
from memory import load_memory, save_memory, get_user_id, manage_memory
from search import google_search, extract_google_leads, groq_search, extract_groq_leads, filter_leads_with_groq
from chathun import chat_with_groq
from config import GOOGLE_API_KEY, GOOGLE_CX, GROQ_API_KEY, MEMORY_FILE
from ml_filter import LeadScorer
import json
import re

def main():
    st.set_page_config(page_title="Lead Intelligence Pro", layout="wide")
    st.title("🚀 AI-Powered Lead Intelligence Platform")

    # Initialize session state variables
    if 'show_raw_results' not in st.session_state:
        st.session_state.show_raw_results = False
    if 'temp_threshold' not in st.session_state:
        st.session_state.temp_threshold = None

    # Initialize ML lead scorer
    lead_scorer = LeadScorer()

    # Initialize memory
    user_id = get_user_id()
    memory = load_memory()

    col1, col2 = st.columns([2, 1])  # Left: Lead Intelligence | Right: Chat Analyst

    # ------------------- Lead Intelligence Dashboard -------------------
    with col1:
        st.header("🔍 Lead Discovery Engine")
        with st.sidebar:
            st.header("⚙️ Configuration")
            with st.expander("API Settings"):
                st.text_input("Google API Key", value=GOOGLE_API_KEY, type="password", key="google_key")
                st.text_input("Google CX", value=GOOGLE_CX, key="cx")
                st.text_input("Groq API Key", value=GROQ_API_KEY, type="password", key="groq_key")
                use_groq_search = st.checkbox("Include Groq Search Results", value=True)

            with st.expander("AI Settings"):
                # Use temporary threshold if set, otherwise use slider value
                current_threshold = st.session_state.temp_threshold if st.session_state.temp_threshold is not None else 70
                min_confidence = st.slider("Minimum Confidence Score", 50, 100, current_threshold)
                max_leads = st.slider("Max Leads to Display", 5, 50, 15)

            if st.button("🧹 Clear Chat History", help="Reset conversation history"):
                if user_id in memory:
                    del memory[user_id]
                    with open(MEMORY_FILE, 'w') as f:
                        json.dump(memory, f)
                    st.session_state.messages = [
                        {"role": "system", "content": "You are a lead intelligence analyst."},
                        {"role": "assistant", "content": "I'm ready to analyze new leads. What opportunities are we exploring today?"}
                    ]
                    st.rerun()

        # Lead Search Interface
        user_query = st.text_input("Describe your ideal lead opportunity:", 
                                 placeholder="e.g. Manufacturing companies seeking automation solutions")
        
        if st.button("🚀 Find High-Quality Leads", key="main_search_button", use_container_width=True):
            if user_query:
                with st.status("🔍 Hunting for premium leads...", expanded=True) as status:
                    # Google Search
                    st.write("🌐 Scanning Google for opportunities...")
                    google_raw = google_search(user_query)
                    google_leads = extract_google_leads(google_raw)
                    
                    # Groq Search
                    groq_leads = []
                    if use_groq_search:
                        st.write("🤖 Querying business databases...")
                        groq_raw = groq_search(user_query)
                        groq_leads = extract_groq_leads(groq_raw)
                    
                    all_leads = google_leads + groq_leads
                    
                    if not all_leads:
                        st.warning("No leads found. Try broadening your search.")
                        status.update(label="Search completed", state="complete", expanded=False)
                        return
                    
                    # AI Filtering
                    st.write("🧠 Analyzing lead quality with AI...")
                    filtered = filter_leads_with_groq(user_query, all_leads)
                    status.update(label="Analysis complete!", state="complete", expanded=False)
                
                # Process and display leads
                st.subheader("💎 Premium Lead Board")
                
                if filtered:
                    leads_data = []
                    for lead in filtered.split('\n\n'):
                        if not lead.strip():
                            continue
                        
                        lines = [line.strip() for line in lead.split('\n') if line.strip()]
                        if not lines:
                            continue
                            
                        lead_data = {
                            "name": lines[0].replace("[", "").replace("]", ""),
                            "details": "\n".join(lines[1:]),
                            "raw_text": lead,
                            "url": next((line.split("URL:")[1].strip() for line in lines if "URL:" in line), None)
                        }
                        
                        try:
                            lead_data["confidence"] = lead_scorer.predict_proba(lead_data["raw_text"])
                        except Exception as e:
                            st.warning(f"ML scoring failed for one lead: {str(e)}")
                            lead_data["confidence"] = 0.5
                        
                        leads_data.append(lead_data)
                    
                    df = pd.DataFrame(leads_data)
                    df = df[df["confidence"] >= (min_confidence/100)]
                    df = df.sort_values("confidence", ascending=False)
                    
                    if len(df) > 0:
                        # Display high-confidence leads
                        st.dataframe(
                            df[["name", "confidence", "details"]],
                            column_config={
                                "name": st.column_config.TextColumn(
                                    "Company/Contact",
                                    width="medium"
                                ),
                                "confidence": st.column_config.ProgressColumn(
                                    "Confidence Score",
                                    format="%.0f%%",
                                    min_value=0,
                                    max_value=1,
                                    width="small"
                                ),
                                "details": st.column_config.TextColumn(
                                    "Key Details",
                                    width="large"
                                )
                            },
                            hide_index=True,
                            use_container_width=True,
                            height=min(400, 50 + len(df) * 35)
                        )
                        # Lead details explorer
                        st.subheader("🔬 Lead Deep Dive")
                        selected_idx = st.selectbox(
                            "Select lead to analyze:",
                            range(len(df)),
                            format_func=lambda x: f"{df.iloc[x]['name']} ({int(df.iloc[x]['confidence']*100)}%)"
                        )
                        
                        with st.expander("📊 Full Lead Analysis", expanded=True):
                            st.markdown(f"### {df.iloc[selected_idx]['name']}")
                            st.markdown(f"**AI Confidence:** {int(df.iloc[selected_idx]['confidence']*100)}%")
                            st.markdown("**Details:**")
                            st.markdown(df.iloc[selected_idx]['details'])
                            if df.iloc[selected_idx]['url']:
                                st.markdown(f"[🔗 Source URL]({df.iloc[selected_idx]['url']})")
                            
                            with st.spinner("Generating strategic insights..."):
                                try:
                                    insights = chat_with_groq([
                                        {"role": "system", "content": "Provide 3 bullet points of strategic advice for engaging this lead"},
                                        {"role": "user", "content": f"Lead: {df.iloc[selected_idx]['raw_text']}"}
                                    ])
                                    st.markdown("### 🧠 Strategic Recommendations")
                                    st.markdown(insights)
                                except Exception as e:
                                    st.error(f"Couldn't generate insights: {str(e)}")
                        
                        st.download_button(
                            label="📥 Export Lead Portfolio",
                            data=df.to_csv(index=False),
                            file_name=f"leads_{user_query[:20]}.csv",
                            mime="text/csv",
                            key="download_button"
                        )
                    else:
                        # Show leads below threshold with improved UI
                        with st.expander("⚠️ Leads Below Confidence Threshold", expanded=True):
                            st.warning(f"""
                            **{len(leads_data)} potential leads found, but none meet your {min_confidence}% confidence threshold.**
                            
                            Recommended actions:
                            """)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("🔄 Lower Threshold", help="Reduce confidence requirement to see more leads"):
                                    st.session_state.temp_threshold = max(min_confidence - 10, 30)
                                    st.rerun()
                            
                            with col2:
                                if st.button("🔍 View Raw Results", help="See unfiltered search results"):
                                    st.session_state.show_raw_results = True
                                    st.rerun()
                            
                            with col3:
                                if st.button("📝 Better Keywords", help="Get AI suggestions for improved search terms"):
                                    with st.spinner("Generating better search terms..."):
                                        search_tips = chat_with_groq([
                                            {"role": "system", "content": "Suggest 3 improved search queries to find better leads"},
                                            {"role": "user", "content": f"My current search: '{user_query}' found {len(leads_data)} low-confidence leads. Suggest better search terms."}
                                        ])
                                        st.info("**AI Suggested Search Terms:**\n\n" + search_tips)
                            
                            # Enhanced lead display table
                            st.markdown("### Marginal Leads (Below Threshold)")
                            below_threshold_df = pd.DataFrame(leads_data)
                            below_threshold_df['cleaned_details'] = below_threshold_df['details'].apply(
                                lambda x: "\n".join([line for line in x.split("\n") if not line.startswith("ML Confidence")])
                            )
                            
                            st.dataframe(
                                below_threshold_df[["name", "confidence", "cleaned_details"]],
                                column_config={
                                    "name": st.column_config.TextColumn(
                                        "Company/Contact",
                                        width="medium"
                                    ),
                                    "confidence": st.column_config.ProgressColumn(
                                        "Confidence Score",
                                        format="%.0f%%",
                                        min_value=0,
                                        max_value=1,
                                        width="small"
                                    ),
                                    "cleaned_details": st.column_config.TextColumn(
                                        "Key Details",
                                        width="large"
                                    )
                                },
                                hide_index=True,
                                use_container_width=True,
                                height=min(400, 50 + len(below_threshold_df) * 35)
                            )
                            
                            # Threshold adjustment
                            st.markdown("---")
                            new_threshold = st.slider(
                                "Temporarily adjust confidence threshold",
                                min_value=0,
                                max_value=min_confidence-1,
                                value=max(min_confidence-20, 30),
                                key="threshold_adjuster"
                            )
                            
                            if st.button(f"🔄 Apply {new_threshold}% Threshold", type="primary"):
                                st.session_state.temp_threshold = new_threshold
                                st.rerun()
                
                # Raw results view
                if st.session_state.show_raw_results:
                    st.subheader("🌐 Raw Search Results")
                    for lead in all_leads:
                        with st.container(border=True):
                            st.markdown(f"### {lead['title']}")
                            st.markdown(lead['snippet'])
                            st.markdown(f"[🔗 Source Link]({lead['url']})")
                    if st.button("← Back to Lead Analysis"):
                        st.session_state.show_raw_results = False
                        st.rerun()

    # ------------------- AI Analyst Chat -------------------
    with col2:
        st.header("💬 AI Strategy Analyst")
        
        # Initialize chat
        if "messages" not in st.session_state:
            if user_id in memory and "conversation" in memory[user_id]:
                st.session_state.messages = memory[user_id]["conversation"]
                st.success("Loaded previous analysis session")
            else:
                st.session_state.messages = [
                    {"role": "system", "content": "You are a lead intelligence analyst. Provide strategic insights about lead opportunities."},
                    {"role": "assistant", "content": "I'm ready to analyze lead opportunities. What shall we examine today?"}
                ]
        
        # Display chat history
        for message in st.session_state.messages[1:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about lead strategy..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    try:
                        response = chat_with_groq(st.session_state.messages)
                        if not response or len(response) < 10:
                            response = "I couldn't generate a quality response. Please rephrase or ask about something else."
                        
                        if 'df' in locals() and len(df) > 0:
                            response += f"\n\n*Based on analysis of {len(df)} high-potential leads*"
                        
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = f"Analysis error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            # Save conversation
            st.session_state.messages = manage_memory(st.session_state.messages)
            save_memory(user_id, st.session_state.messages)

if __name__ == "__main__":
    main()