import streamlit as st
import time
from .evaluator import model # Reusing the model from evaluator

def render_chat_interface(evaluation_results, selected_candidate=None, extracted_texts=None, mock_mode=False):
    """
    Render the Exploration Chat interface.
    `evaluation_results` is a list of dictionaries containing the scored results.
    """
    st.markdown("### 💬 Exploration Chat")
    st.caption("Ask follow-up questions about the evaluated candidates.")
    
    if not evaluation_results:
        st.info("Upload and process resumes first to chat about them.")
        return

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask about the candidates... (e.g., 'Who has the most Python experience?')"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Construct Summary Context string
        if selected_candidate and extracted_texts and selected_candidate in extracted_texts:
            context_str = f"CONTEXT - Currently Viewing Profile: {selected_candidate}\n"
            context_str += "Full Resume Text:\n---\n"
            context_str += extracted_texts[selected_candidate] + "\n---\n\n"
        else:
            context_str = "CONTEXT - Scored Candidate Results Summary:\n"
            for res in evaluation_results:
                skills_str = ", ".join(res.get('matched_skills', [])) if isinstance(res.get('matched_skills'), list) else res.get('matched_skills', '')
                context_str += f"- Name: {res.get('name')}\n  Score: {res.get('score')}\n  Skills: {skills_str}\n  Verdict: {res.get('experience_verdict')}\n\n"
            
        # Use a Window for chat history (last 6 messages to remember context but save tokens)
        recent_messages = st.session_state.messages[-6:]
        history_str = "RECENT CHAT HISTORY:\n"
        for msg in recent_messages:
            # Don't include the current prompt in the history string again
            if msg["content"] != prompt:
                history_str += f"{msg['role'].upper()}: {msg['content']}\n"

        full_prompt = f"""
        You are an HR AI Assistant. Use the following context (candidate summaries) and recent chat history to answer the user's question.
        If the answer is not in the context, kindly state that you don't know based on the provided resumes.
        
        {context_str}
        
        {history_str}
        
        User Question: {prompt}
        """

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            if mock_mode:
                time.sleep(0.5)
                dummy_response = f"[MOCK MODE] I am a local mock assistant. You asked: '{prompt}'. I have no real answer since I am completely local and saving your API quota."
                message_placeholder.markdown(dummy_response)
                st.session_state.messages.append({"role": "assistant", "content": dummy_response})
            else:
                # Robust retry logic for rate limits (429)
                max_retries = 5
                retry_delay = 15
                
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            message_placeholder.info(f"⏳ Rate limit hit. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                            time.sleep(retry_delay)
                            
                        response = model.generate_content(full_prompt)
                        message_placeholder.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                        break # Success, exit retry loop
                        
                    except Exception as e:
                        if "429" in str(e) and attempt < max_retries - 1:
                            continue # Go to next attempt
                        else:
                            error_msg = f"Sorry, I encountered an error: {e}"
                            message_placeholder.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                            break
