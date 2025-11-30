import streamlit as st
import ollama
import requests
import pdfplumber
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
        soup = BeautifulSoup(response.text, 'html.parser')
        
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
            "text": soup.get_text(separator=' ')[:20000],
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
        return {"text": text[:20000], "error": None}
    except Exception as e:
        return {"error": str(e)}

# --- 3. UI SETUP ---
if "context_text" not in st.session_state:
    st.session_state.context_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "found_files" not in st.session_state:
    st.session_state.found_files = []

with st.sidebar:
    st.header("🕵️ Data Source")
    mode = st.radio("Input Type:", ["🌐 Website URL", "📄 Upload PDF"])
    
    if mode == "🌐 Website URL":
        url = st.text_input("Enter URL:")
        if st.button("Load Website") and url:
            with st.spinner("Scraping..."):
                data = fetch_webpage_data(url)
                if data.get("error"):
                    st.error(data["error"])
                else:
                    st.session_state.context_text = data["text"]
                    st.session_state.found_files = data["files"] # Save files
                    st.session_state.messages = []
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
                    st.session_state.found_files = [] # Clear files for PDF mode
                    st.session_state.messages = []
                    st.success("PDF Loaded!")

    # Show Files found (Only for Website mode)
    if st.session_state.found_files:
        st.divider()
        st.subheader("📂 Found Files")
        for f in st.session_state.found_files:
            st.markdown(f"[{f['text']}]({f['url']})")

# --- 4. CHAT ---
st.title("AI Research Assistant")

if not st.session_state.context_text:
    st.info("👈 Please load a data source.")
    st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_prompt = f"Answer strictly based on:\n{st.session_state.context_text}"
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # 1. Define message history
            api_messages = [{'role': 'system', 'content': system_prompt}] + st.session_state.messages
            
            # 2. Call Ollama with SMARTER model + MAX memory
            response = ollama.chat(
                model='llama3.1',  # <--- CHANGED to 3.1 (Smart 8B Model)
                messages=api_messages,
                options={
                    'num_ctx': 32768,  # Max memory for 8GB GPU
                    'temperature': 0.7 
                }
            )
            
            # 3. Display result
            ai_reply = response['message']['content']
            st.markdown(ai_reply)
            
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})