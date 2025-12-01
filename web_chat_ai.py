import sys
import requests
from bs4 import BeautifulSoup
import ollama

def fetch_webpage_text(url: str) -> str:
    """Scrapes the URL and returns clean, readable text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cleanup: Remove non-content tags
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        text = soup.get_text()
        
        # Advanced Cleanup: Collapse multiple newlines into one
        lines = (line.strip() for line in text.splitlines())
        clean_text = '\n'.join(line for line in lines if line)
        
        # INCREASED LIMIT: 100k chars to match your 32k token memory
        return clean_text[:100000] 
        
    except Exception as e:
        print(f"❌ Error fetching URL: {e}")
        return ""

def chat_loop(context_text: str):
    """Starts an interactive session with the scraped content."""
    
    print("\n✅ content loaded! You can now ask questions about this website.")
    print("Type 'exit' or 'quit' to stop.\n")
    
    system_prompt = f"""
    You are a helpful research assistant. 
    Answer the user's questions strictly based on the provided WEBSITE CONTENT below.
    If the answer is not in the text, simply say "I couldn't find that in the article."
    
    WEBSITE CONTENT:
    {context_text}
    """
    
    messages = [{'role': 'system', 'content': system_prompt}]

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("👋 Exiting chat.")
            break
            
        messages.append({'role': 'user', 'content': user_input})
        
        print("🤖 Thinking...")
        # UPDATED: Using Llama 3.1 + 32k Context
        response = ollama.chat(
            model='llama3.1', 
            messages=messages,
            options={'num_ctx': 32768}
        )
        ai_reply = response['message']['content']
        
        print(f"\nAI: {ai_reply}\n")
        messages.append({'role': 'assistant', 'content': ai_reply})

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("🔗 Enter a URL to chat with: ")
        
    if not url.startswith("http"):
        print("Please enter a valid URL.")
        return

    print(f"🌍 Fetching: {url}...")
    clean_text = fetch_webpage_text(url)
    
    if clean_text:
        chat_loop(clean_text)

if __name__ == "__main__":
    main()