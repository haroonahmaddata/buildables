"""
Main Streamlit application for the Multi-Agent Medium Article Generator.
This is the primary entry point for the web interface.
"""

import streamlit as st
import time
from workflow_backend import workflow_manager

# Configure Streamlit page
st.set_page_config(
    page_title="Multi-Agent Medium Article Generator",
    page_icon="📝",
    layout="wide"
)

def display_workflow_progress(current_step: str):
    """Display the current workflow progress"""
    steps = ["research", "generate", "fact_check", "HUMAN_REVIEW", "reflect"]
    step_names = ["🔍 Research", "✍️ Generate", "✅ Fact Check", "👤 Human Review", "🤔 Reflect"]
    
    cols = st.columns(len(steps))
    for i, (step, name) in enumerate(zip(steps, step_names)):
        with cols[i]:
            if step == current_step:
                st.success(f"**{name}**")
            elif current_step in steps and steps.index(current_step) > i:
                st.success(name)
            else:
                st.info(name)

# Main UI
st.title("🤖 Multi-Agent Medium Article Generator")
st.markdown("Generate high-quality Medium articles using AI agents with research, fact-checking, and human oversight.")

# Sidebar for workflow control
with st.sidebar:
    st.header("Workflow Control")
    
    if st.button("🔄 Reset Workflow"):
        workflow_manager.reset_workflow()
        st.rerun()
    
    st.markdown("---")
    st.subheader("Current State")
    status = workflow_manager.get_workflow_status()
    st.write(f"**Messages in state:** {status['message_count']}")
    st.write(f"**Current step:** {status['current_step'] or 'Not started'}")
    st.write(f"**Complete:** {status['is_complete']}")
    
    st.markdown("---")
    st.subheader("About")
    st.markdown("""
    **Multi-Agent System:**
    - 🔍 Research with Tavily Search
    - ✍️ Generate with Gemini 2.0-flash
    - ✅ Fact-check for accuracy
    - 👤 Human review & feedback
    - 🤔 Reflect & improve
    """)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Article Topic")
    
    # Topic input
    topic = st.text_area(
        "Enter your Medium article topic:",
        placeholder="e.g., 'Top 10 ways to become financially independent'",
        height=100
    )
    
    # Example topics
    st.markdown("**Example topics:**")
    example_topics = [
        "How to build a personal brand in tech",
        "The future of remote work in 2025",
        "Beginner's guide to cryptocurrency investing",
        "10 productivity hacks for developers"
    ]
    
    for example in example_topics:
        if st.button(f"💡 {example}", key=f"example_{example}"):
            st.session_state.example_topic = example
            st.rerun()
    
    # Use example topic if selected
    if hasattr(st.session_state, 'example_topic'):
        topic = st.session_state.example_topic
        del st.session_state.example_topic
    
    # Start workflow button
    if st.button("🚀 Generate Article", type="primary", disabled=not topic.strip()):
        workflow_manager.initialize_workflow(topic.strip())
        st.rerun()

with col2:
    st.header("🔄 Workflow Progress")
    
    status = workflow_manager.get_workflow_status()
    if status['current_step']:
        display_workflow_progress(status['current_step'])
        
        # Auto-run workflow steps (except human review)
        if status['current_step'] not in ["HUMAN_REVIEW", "END"] and not status['current_step'].startswith("ERROR"):
            with st.spinner(f"Running {status['current_step']}..."):
                time.sleep(1)  # Brief pause for UI
                new_state, next_step = workflow_manager.run_single_step()
                st.rerun()

# Content display area
if workflow_manager.workflow_state:
    st.markdown("---")
    st.header("📄 Generated Content")
    
    # Create tabs for different content types
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Research", "📝 Article", "✅ Fact Check", "🤔 Reflection"])
    
    with tab1:
        research_content = workflow_manager.extract_content("research")
        st.markdown("### Research Results")
        if research_content != "Content not available yet":
            st.text_area("Research findings:", research_content, height=200, disabled=True)
            # Show research sources count
            if "Research on" in research_content:
                source_count = research_content.count("...")
                st.info(f"📊 Found {source_count} research sources")
        else:
            st.info("Research will appear here once the research agent completes...")
    
    with tab2:
        article_content = workflow_manager.extract_content("article")
        st.markdown("### Generated Article")
        if article_content != "Content not available yet":
            st.text_area("Article content:", article_content, height=400, disabled=True)
            # Show article stats
            word_count = len(article_content.split())
            char_count = len(article_content)
            st.info(f"📊 {word_count} words, {char_count} characters")
        else:
            st.info("Article will appear here once the generation agent completes...")
    
    with tab3:
        fact_check_content = workflow_manager.extract_content("fact_check")
        st.markdown("### Fact Check Results")
        if fact_check_content != "Content not available yet":
            st.text_area("Fact check feedback:", fact_check_content, height=200, disabled=True)
        else:
            st.info("Fact-check results will appear here once the fact-check agent completes...")
    
    with tab4:
        reflection_content = workflow_manager.extract_content("reflection")
        st.markdown("### Reflection & Critique")
        if reflection_content != "Content not available yet":
            st.text_area("AI reflection:", reflection_content, height=200, disabled=True)
        else:
            st.info("Reflection will appear here once the reflection agent completes...")

# Human Review Interface
if status['needs_human_review']:
    st.markdown("---")
    st.header("👤 Human Review Required")
    st.info("The AI has generated an article and fact-checked it. Please review and provide feedback.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Current Article")
        current_article = workflow_manager.extract_content("article")
        st.text_area("Review this article:", current_article, height=300, disabled=True)
        
        st.markdown("### Fact Check Feedback")
        fact_check = workflow_manager.extract_content("fact_check")
        st.text_area("Fact checker notes:", fact_check, height=150, disabled=True)
    
    with col2:
        st.markdown("### Your Feedback")
        feedback_options = [
            "Approve and continue",
            "Revise: Make it shorter",
            "Revise: Add more examples", 
            "Revise: Improve the hook",
            "Revise: Make it more engaging",
            "Revise: Fix factual issues",
            "Custom feedback"
        ]
        
        selected_feedback = st.selectbox("Choose feedback type:", feedback_options)
        
        if selected_feedback == "Custom feedback":
            custom_feedback = st.text_area("Enter custom feedback:", height=100, 
                                         placeholder="Be specific about what you'd like changed...")
            final_feedback = custom_feedback
        else:
            final_feedback = selected_feedback
        
        if st.button("✅ Submit Feedback", type="primary"):
            if final_feedback.strip():
                workflow_manager.process_human_feedback(final_feedback)
                st.success("Feedback submitted! The AI will now reflect and improve the article.")
                st.rerun()
            else:
                st.warning("Please provide feedback before submitting.")

# Final result
if status['is_complete']:
    st.markdown("---")
    st.success("🎉 Article generation completed!")
    
    final_article = workflow_manager.extract_content("article")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Final Article")
        st.markdown(final_article)
    
    with col2:
        st.markdown("### Export Options")
        st.download_button(
            label="📥 Download as Markdown",
            data=final_article,
            file_name="generated_article.md",
            mime="text/markdown"
        )
        
        # Copy to clipboard button (using JavaScript)
        if st.button("📋 Copy to Clipboard"):
            st.code(final_article, language="markdown")
            st.info("Article displayed above - you can select and copy it!")

# Error handling
if status['current_step'] and status['current_step'].startswith("ERROR"):
    st.error(f"Workflow Error: {status['current_step']}")
    st.info("Try resetting the workflow and starting again.")

# Footer
st.markdown("---")
st.markdown("*Powered by LangGraph, Google Gemini 2.0-flash, and Tavily Search*")
st.markdown("Built with ❤️ using multi-agent AI workflows")
