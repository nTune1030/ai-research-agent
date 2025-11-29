import streamlit as st
import ollama
import requests
from bs4 import BeautifulSoup

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AI Research Agent", page_icon="🕵️")

# --- 2. BACKEND FUNCTIONS (Reused from your script) ---
def fetch_webpage_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cleanup
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        return soup.get_text(separator=' ')[:12000] # Limit context
    except Exception as e:
        return f"Error: {e}"

# --- 3. SESSION STATE MANAGEMENT ---
# Streamlit re-runs the script on every click. We use "Session State"
# to remember data (like the chat history) between those re-runs.

if "messages" not in st.session_state:
    st.session_state.messages = []

if "context_text" not in st.session_state:
    st.session_state.context_text = ""

# --- 4. SIDEBAR (The Control Panel) ---
with st.sidebar:
    st.header("🕵️ Research Controls")
    url_input = st.text_input("Enter URL to Analyze:", placeholder="https://example.com")
    
    if st.button("Load Website"):
        with st.spinner("Scraping and processing..."):
            text = fetch_webpage_text(url_input)
            if "Error" in text:
                st.error(text)
            else:
                st.session_state.context_text = text
                # Clear old chat history when loading a new site
                st.session_state.messages = []
                st.success("Website Loaded! You can now chat.")
                
    st.divider()
    st.markdown("**Debug Info:**")
    st.caption(f"Context Length: {len(st.session_state.context_text)} characters")

# --- 5. MAIN CHAT INTERFACE ---
st.title("AI Research Assistant")

# Warning if no website is loaded
if not st.session_state.context_text:
    st.info("👈 Please enter a URL in the sidebar to start.")
    st.stop() # Stop execution here until data is ready

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle User Input
if prompt := st.chat_input("Ask a question about the article..."):
    # 1. Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Build the "System Prompt" dynamically
    # We inject the scraped text into the system prompt for every message
    system_prompt = f"""
    You are a helpful research assistant.
    Answer strictly based on the provided text.
    
    TEXT DATA:
    {st.session_state.context_text}
    """
    
    # 3. Call Ollama
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # We send the System Prompt + History
            api_messages = [{'role': 'system', 'content': system_prompt}] + st.session_state.messages
            
            response = ollama.chat(model='llama3.2', messages=api_messages)
            ai_reply = response['message']['content']
            st.markdown(ai_reply)
            
    # 4. Save AI response to history
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})