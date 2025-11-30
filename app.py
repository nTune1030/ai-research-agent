import streamlit as st
import ollama
import requests
from bs4 import BeautifulSoup
import pdfplumber

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AI Research Agent", page_icon="🕵️")

# --- 2. BACKEND FUNCTIONS ---
def fetch_webpage_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        return soup.get_text(separator=' ')[:20000]
    except Exception as e:
        return f"Error fetching URL: {e}"

def extract_pdf_text(uploaded_file):
    try:
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text[:20000]
    except Exception as e:
        return f"Error reading PDF: {e}"

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_text" not in st.session_state:
    st.session_state.context_text = ""

# --- 4. SIDEBAR (CONTROLS) ---
with st.sidebar:
    st.header("🕵️ Data Source")
    source_mode = st.radio("Select Input Type:", ["🌐 Website URL", "📄 Upload PDF"])
    
    if source_mode == "🌐 Website URL":
        url_input = st.text_input("Enter URL:", placeholder="https://example.com")
        if st.button("Load Website"):
            with st.spinner("Scraping..."):
                text = fetch_webpage_text(url_input)
                # FIX: Check if the string STARTS with Error, instead of containing it
                if text.startswith("Error"):
                    st.error(text)
                else:
                    st.session_state.context_text = text
                    st.session_state.messages = [] 
                    st.success("Website Loaded!")

    elif source_mode == "📄 Upload PDF":
        uploaded_file = st.file_uploader("Drop a PDF here", type="pdf")
        if uploaded_file is not None:
            if st.button("Process PDF"):
                with st.spinner("Reading PDF..."):
                    text = extract_pdf_text(uploaded_file)
                    
                    # FIX: Strict check so we don't flag valid text as an error
                    if text.startswith("Error reading PDF:"):
                        st.error(text)
                    else:
                        st.session_state.context_text = text
                        st.session_state.messages = []
                        st.success("PDF Loaded Successfully!")

    st.divider()
    # Debug info to confirm data is actually loaded
    # st.caption(f"Context in Memory: {len(st.session_state.context_text)} chars")

# --- 5. MAIN CHAT ---
st.title("AI Research Assistant")

if not st.session_state.context_text:
    st.info("👈 Use the sidebar to load a Website or PDF to get started.")
    st.stop()

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask a question about the document..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    system_prompt = f"""
    You are a helpful research assistant.
    Answer strictly based on the provided text below.
    If the answer is not in the text, say "I cannot find that information in the document."
    
    DOCUMENT TEXT:
    {st.session_state.context_text}
    """
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            api_messages = [{'role': 'system', 'content': system_prompt}] + st.session_state.messages
            response = ollama.chat(model='llama3.2', messages=api_messages)
            ai_reply = response['message']['content']
            st.markdown(ai_reply)
            
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})