import re
import streamlit as st
import pandas as pd
from chathun import chat_with_groq
import psycopg2
from psycopg2 import Error
from datetime import datetime


def save_lead_to_database(lead, details, contact_info):
     try:
         conn = psycopg2.connect(
             host="localhost",
             database="admin",
             user="postgres",
             password="postgres",
             port="5432"
         )
         cursor = conn.cursor()
         # Extract email and phone from contact_info
         email_match = re.search(r'[\w\.-]+@[\w\.-]+', contact_info)
         phone_match = re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|`latex:\(\d{3}\)`\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})', contact_info)

         email_from = email_match.group() if email_match else ''
         phone = phone_match.group() if phone_match else ''

         insert_query = """ INSERT INTO crm_lead (name, contact_name, website, phone, email_from, description, create_date, type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """

         cursor.execute(insert_query, ( lead['name'], 
    lead['name'], 
    lead.get('url', ''), 
    phone, 
    email_from, 
    details, 
    datetime.now(), 
    'lead'
))
         conn.commit()
         st.success("Lead saved to database.")

     except Error as e:
         st.error(f"Error inserting lead: {e}")
         if conn:
             conn.rollback()
     finally:
         if conn:
             cursor.close()
             conn.close()

def display_leads(leads, search_query):
    """Display leads and handle selection"""
    # Initialize saved leads table in session state
    if 'saved_leads' not in st.session_state:
        st.session_state.saved_leads = pd.DataFrame(columns=['Company', 'Website', 'Contact', 'Details'])
    
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
            display_lead_details(leads[selected_index], search_query)
    
    # Display saved leads table and export button
    if not st.session_state.saved_leads.empty:
        st.divider()
        st.subheader("📋 Your Saved Leads")
        
        # Enhanced table display with clickable links
        st.dataframe(
            st.session_state.saved_leads,
            column_config={
                "Company": st.column_config.TextColumn(width="medium"),
                "Website": st.column_config.LinkColumn("Website"),
                "Contact": st.column_config.TextColumn(),
                "Details": st.column_config.TextColumn(width="large")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Export button
        export_cols = st.columns(3)
        with export_cols[1]:
            st.download_button(
                "💾 Export to Excel",
                data=st.session_state.saved_leads.to_csv(index=False),
                file_name="saved_leads.csv",
                mime="text/csv",
                use_container_width=True
            )

def display_lead_details(lead, search_query):
    """Show detailed information about a single lead"""
    st.subheader(lead['name'])
    
    with st.expander("📌 Lead Details", expanded=True):
        # Extract contact info from details (simple pattern matching)
        contact_info = "Not found"
        details = lead.get('details', '')
        
        # Try to find email or phone
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', details)
        phone_match = re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})', details)
        
        contact_info = ""
        if email_match:
            contact_info += f"📧 {email_match.group()}"
        if phone_match:
            contact_info += f" 📞 {phone_match.group()}"
        if not contact_info:
            contact_info = "Not specified"
        
        # Display fields
        if 'industry' in lead:
            st.markdown(f"**Industry:** {lead['industry']}")
        
        st.markdown(f"**Contact:** {contact_info}")
        st.markdown(f"**Details:** {details}")
        
        if 'url' in lead and lead['url']:
            st.markdown(f"[🌐 Visit Website]({lead['url']})")
        
        # Add to list button
    # Add to list button
            # Add to list button
        if st.button("➕ Add to List", key=f"add_{lead['name']}_{search_query}"):
        
            save_lead_to_database(lead, details, contact_info)
            new_lead = {
                'Company': lead['name'],
                'Website': lead.get('url', ''),
                'Contact': contact_info,
                'Details': details
            }

            # Convert to DataFrame and concatenate
            new_df = pd.DataFrame([new_lead])
            st.session_state.saved_leads = pd.concat(
                [st.session_state.saved_leads, new_df],
                ignore_index=True
            )
            st.success(f"Added {lead['name']} to your list!")

                
        # Generate AI insights
        with st.spinner("Generating engagement recommendations..."):
            prompt = [
                {"role": "system", "content": "You are a lead engagement strategist."},
                {"role": "user", "content": f"Suggest contact approach for: {lead['name']}\nDetails: {details}"}
            ]
            insights = chat_with_groq(prompt)
            st.markdown("### 💡 Engagement Strategy")
            st.markdown(insights)