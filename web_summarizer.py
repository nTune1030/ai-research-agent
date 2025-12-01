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
        
        # Remove script and style elements (garbage text)
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        clean_text = '\n'.join(line for line in lines if line)
        
        return clean_text[:100000] 
        
    except Exception as e:
        print(f"❌ Error fetching URL: {e}")
        return ""

def summarize_text(text: str):
    """Sends text to Ollama for a bullet-point summary."""
    print("⏳ AI is reading and summarizing...")
    
    prompt = f"""
    Analyze the following website text and provide a concise summary.
    Format the output as:
    1. A one-sentence 'Main Idea'.
    2. A list of 3-5 key bullet points.
    
    TEXT:
    {text}
    """
    
    response = ollama.chat(
        model='llama3.1',
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        options={'num_ctx': 32768}
    )
    
    print("\n" + "="*40)
    print(response['message']['content'])
    print("="*40)

def main():
    # Allow user to pass URL as command line argument, or ask for it
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("🔗 Enter a URL to summarize: ")
        
    if not url.startswith("http"):
        print("Please enter a valid URL (starting with http/https).")
        return

    print(f"🌍 Fetching: {url}...")
    clean_text = fetch_webpage_text(url)
    
    if clean_text:
        summarize_text(clean_text)

if __name__ == "__main__":
    main()