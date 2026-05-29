import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import base64
from streamlit_pdf_viewer import pdf_viewer

def render_dashboard(results):
    """
    Render the Plotly dashboard given the evaluation results.
    `results` is a list of dictionaries with Name, Score, Matched Skills, and Experience Verdict.
    """
    if not results:
        st.info("No candidates evaluated yet. Please upload resumes and process them.")
        return

    df = pd.DataFrame(results)
    
    # Categorize into Selected and Rejected based on Score > 75
    df['Status'] = df['score'].apply(lambda x: 'Selected' if x > 75 else 'Rejected')

    st.markdown("### 📊 Status Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for Selected vs Rejected
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        # Premium color scheme
        color_map = {'Selected': '#00CC96', 'Rejected': '#EF553B'}
        
        fig_pie = px.pie(
            status_counts, 
            names='Status', 
            values='Count', 
            title="Candidate Selection Status",
            color='Status',
            color_discrete_map=color_map,
            hole=0.4
        )
        fig_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            margin=dict(t=40, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_pie, width='stretch')
        
    with col2:
        # Bar chart for Score Distribution
        fig_bar = px.bar(
            df.sort_values(by='score', ascending=False),
            x='name',
            y='score',
            title="Candidate Scores",
            color='Status',
            color_discrete_map=color_map,
            text='score'
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            margin=dict(t=40, b=0, l=0, r=0),
            yaxis=dict(range=[0, 105]) # Give some headroom for text
        )
        st.plotly_chart(fig_bar, width='stretch')

    st.markdown("---")
    st.markdown("### 📈 Skills Analysis")
    
    # Calculate average score per skill
    df_skills = df.copy()
    # Handle both list and string types for matched_skills
    df_skills['matched_skills'] = df_skills['matched_skills'].apply(lambda x: x if isinstance(x, list) else [x] if isinstance(x, str) and x else [])
    df_skills = df_skills.explode('matched_skills')
    
    if not df_skills.empty and 'matched_skills' in df_skills.columns:
        # Filter out empty skills
        df_skills = df_skills[df_skills['matched_skills'].astype(bool)]
        if not df_skills.empty:
            skill_avg = df_skills.groupby('matched_skills')['score'].mean().reset_index()
            skill_avg = skill_avg.rename(columns={'matched_skills': 'Skill', 'score': 'Average Score'})
            skill_avg = skill_avg.sort_values(by='Average Score', ascending=False)
            
            fig_skills = px.bar(
                skill_avg,
                x='Skill',
                y='Average Score',
                title="Average Score per Skill Category",
                color='Average Score',
                color_continuous_scale='blues'
            )
            fig_skills.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                margin=dict(t=40, b=0, l=0, r=0)
            )
            st.plotly_chart(fig_skills, use_container_width=True)
        else:
            st.info("No matching skills found to generate analysis.")

def render_results_table(results):
    """
    Render the candidates in a custom grid to include a 'View Resume' button.
    """
    if not results:
        return
        
    st.markdown("### 📋 Candidate Evaluation Results")
    
    # Headers
    col1, col2, col3, col4, col5 = st.columns([2, 1, 3, 2, 2])
    with col1: st.markdown("**Name**")
    with col2: st.markdown("**Score**")
    with col3: st.markdown("**Matched Skills**")
    with col4: st.markdown("**Status**")
    with col5: st.markdown("**Action**")
    st.markdown("---")
    
    for idx, res in enumerate(results):
        col1, col2, col3, col4, col5 = st.columns([2, 1, 3, 2, 2])
        
        name = res.get('name', 'Unknown')
        score = res.get('score', 0)
        skills = res.get('matched_skills', [])
        skills_str = ", ".join(skills) if isinstance(skills, list) else skills
        status = ':green[✅ Selected]' if score > 75 else ':red[❌ Rejected]'
        
        with col1: st.write(name)
        with col2: st.write(score)
        with col3: st.caption(skills_str)
        with col4: st.markdown(status)
        with col5:
            if st.button("View Resume", key=f"view_{idx}"):
                st.session_state.selected_candidate = name
                st.rerun()
        st.divider()

def render_pdf_viewer(file_bytes):
    """
    Render a PDF file from bytes using streamlit_pdf_viewer.
    """
    pdf_viewer(input=file_bytes, width=700)
