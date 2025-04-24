import streamlit as st
from chathun import chat_with_groq

def display_leads(leads, search_query):
    """Display leads and handle selection"""
    if not leads:
        st.warning("No leads found. Try a different search.")
        return
    
    # Create two columns - one for list, one for details
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Discovered Leads")
        selected_index = st.selectbox(
            "Select a lead:",
            range(len(leads)),
            format_func=lambda i: leads[i]['name'],
            key=f"lead_select_{search_query}"
        )
    
    with col2:
        if selected_index is not None:
            display_lead_details(leads[selected_index])

def display_lead_details(lead):
    """Show detailed information about a single lead"""
    st.subheader(lead['name'])
    
    with st.expander("📌 Lead Details", expanded=True):
        if 'industry' in lead:
            st.markdown(f"**Industry:** {lead['industry']}")
        
        st.markdown(f"**Details:** {lead['details']}")
        
        if 'url' in lead and lead['url']:
            st.markdown(f"[🌐 Visit Website]({lead['url']})")
        
        # Generate AI insights
        with st.spinner("Generating engagement recommendations..."):
            prompt = [
                {"role": "system", "content": "You are a lead engagement strategist. Provide 3 actionable recommendations for contacting this lead."},
                {"role": "user", "content": f"Company: {lead['name']}\nDetails: {lead['details']}"}
            ]
            insights = chat_with_groq(prompt)
            st.markdown("### 💡 Engagement Strategy")
            st.markdown(insights)
    
  