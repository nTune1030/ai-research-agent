"""
AI Research Agent - Local Autonomous Browser & PDF Analyst
----------------------------------------------------------
A Streamlit-based interface that turns a local LLM into an internet-connected research assistant.
It allows users to scrape websites, read PDFs, and autonomously navigate between links.

HARDWARE & CONFIGURATION TWEAKS (Optimized for RTX 5050 / 8GB VRAM):
--------------------------------------------------------------------
1. Model: Llama 3.1 (8B)
   - Chosen over Llama 3.2 (3B) for superior reasoning and instruction following.
   - Fits comfortably in VRAM when quantized (Q4_K_M).

2. Context Window (num_ctx): 20,480 Tokens
   - The theoretical max for Llama 3.1 is 128k, but that requires 24GB+ VRAM.
   - We initially tried 32k (32768), but it caused OOM (Exit Code 2) crashes on 8GB VRAM.
   - 20k is the "Sweet Spot": Maximize document reading capacity without crashing the GPU.

3. Input Truncation: 100,000 Characters
   - We limit scraped text to ~100k chars to roughly align with the 20k token limit.
   - Prevents context overflow and processing lag.

4. GPU Acceleration:
   - Requires `OLLAMA_FLASH_ATTENTION=1` in the launch environment (set in .bat).
   - Offloads 29/29 layers to the GPU for maximum inference speed.

FEATURES:
- Autonomous Navigation: The AI can output JSON commands (`{"action": "navigate"...}`) to click links.
- PDF Analysis: Uses `pdfplumber` for safe text extraction.
- Link Injection: Feeds the top 50 discovered links into the context for the AI to "see".
"""

import streamlit as st
import ollama
import requests
import pdfplumber
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AI Research Agent", page_icon="🕵️", layout="wide")

# --- 2. BACKEND FUNCTIONS ---
def fetch_webpage_data(url):
    """Scrapes text AND extracts links/files."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        # Less CPU
        soup = BeautifulSoup(response.text, 'lxml')
        # Heavy CPU usuage
        # soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- Link Extraction ---
        links = []
        files = []
        target_extensions = {'.pdf', '.txt', '.csv', '.md', '.json', '.docx'}
        
        for link in soup.find_all('a', href=True):
            href = str(link.get('href'))
            text = link.get_text(strip=True) or "[No Text]"
            
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            full_url = urljoin(url, href)
            link_data = {"text": text, "url": full_url}
            
            if any(full_url.lower().endswith(ext) for ext in target_extensions):
                files.append(link_data)
            else:
                links.append(link_data)

        # --- Text Cleanup ---
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        
        return {
            "text": soup.get_text(separator=' ')[:100000],
            "links": links,
            "files": files,
            "error": None
        }
    except Exception as e:
        return {"error": str(e)}

def extract_pdf_text(uploaded_file):
    """Extracts text from PDF."""
    try:
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return {"text": text[:100000], "error": None}
    except Exception as e:
        return {"error": str(e)}

# --- 3. UI SETUP ---
if "context_text" not in st.session_state:
    st.session_state.context_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "found_files" not in st.session_state:
    st.session_state.found_files = []
if "found_links" not in st.session_state:
    st.session_state.found_links = []
if "current_url" not in st.session_state:
    st.session_state.current_url = ""

with st.sidebar:
    st.header("🕵️ Data Source")
    mode = st.radio("Input Type:", ["🌐 Website URL", "📄 Upload PDF"])
    
    # --- HELPER: Function to load data and update UI ---
    def load_new_url(target_url):
        with st.spinner(f"Navigating to: {target_url}..."):
            data = fetch_webpage_data(target_url)
            if data.get("error"):
                st.error(data["error"])
                return False
            else:
                st.session_state.context_text = data["text"]
                st.session_state.found_files = data["files"]
                st.session_state.found_links = data["links"]
                st.session_state.current_url = target_url
                # Add a system note to chat history so the user knows what happened
                st.session_state.messages.append({"role": "assistant", "content": f"✅ **Navigation Successful!** I have loaded the new page: {target_url}"})
                return True

    if mode == "🌐 Website URL":
        url = st.text_input("Enter URL:", value=st.session_state.current_url)
        if st.button("Load Website") and url:
            if load_new_url(url):
                st.success("Website Loaded!")
                    
    elif mode == "📄 Upload PDF":
        pdf_file = st.file_uploader("Upload PDF", type="pdf")
        if st.button("Process PDF") and pdf_file:
            with st.spinner("Reading PDF..."):
                data = extract_pdf_text(pdf_file)
                if data.get("error"):
                    st.error(data["error"])
                else:
                    st.session_state.context_text = data["text"]
                    st.session_state.found_files = []
                    st.session_state.found_links = []
                    st.session_state.current_url = "PDF Upload"
                    st.session_state.messages = []
                    st.success("PDF Loaded!")

    if st.session_state.found_files:
        st.divider()
        st.subheader("📂 Found Files")
        for f in st.session_state.found_files:
            st.markdown(f"[{f['text']}]({f['url']})")

# --- 4. CHAT ---
st.title("AI Research Agent")

if not st.session_state.context_text:
    st.info("👈 Please load a data source.")
    st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question or say 'Go to [Link Name]'..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- MAGIC: Prepare Links for the AI Brain ---
    # We take the top 50 links and format them so the AI can "read" them
    links_context = ""
    if st.session_state.found_links:
        links_context = "\n\nAVAILABLE LINKS ON THIS PAGE:\n"
        for i, link in enumerate(st.session_state.found_links[:50]): # Limit to top 50 to save context
            links_context += f"- {link['text']}: {link['url']}\n"

    system_prompt = f"""
    You are a helpful research assistant.
    Answer strictly based on the provided text.
    
    IMPORTANT: You have the ability to navigate the web.
    If the user asks to "follow", "click", or "go to" a specific link found in the content below,
    reply with EXACTLY this JSON format and nothing else:
    {{ "action": "navigate", "url": "THE_URL_HERE" }}

    TEXT DATA:
    {st.session_state.context_text}

    {links_context}
    """
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # 1. Define message history
            api_messages = [{'role': 'system', 'content': system_prompt}] + st.session_state.messages
            
            # 2. Call Ollama
            response = ollama.chat(
                model='llama3.1', 
                messages=api_messages,
                options={
                    'num_ctx': 20480, # Safer memory load for GPU
                    'temperature': 0.7 
                }
            )
            
            ai_reply = response['message']['content']

            # --- 3. CHECK FOR NAVIGATION COMMAND ---
            # We look for the special JSON trigger
            if '{ "action": "navigate"' in ai_reply or '{"action": "navigate"' in ai_reply:
                try:
                    # Extract the URL using regex to be safe
                    url_match = re.search(r'"url":\s*"([^"]+)"', ai_reply)
                    if url_match:
                        target_url = url_match.group(1)
                        st.markdown(f"🔄 **Navigating to:** `{target_url}`...")
                        
                        # EXECUTE NAVIGATION
                        if load_new_url(target_url):
                            st.rerun() # Restart the app to show new data
                    else:
                        st.error("AI tried to navigate but the URL was broken.")
                except Exception as e:
                    st.error(f"Navigation failed: {e}")
            else:
                # Normal Text Reply
                st.markdown(ai_reply)
            
    if not ('{ "action": "navigate"' in ai_reply):
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})