import json
import requests
from bs4 import BeautifulSoup
import ollama
from datetime import datetime
import os

# URL to scrape
URL = "https://www.npr.org/"

def fetch_clean_text(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
            tag.extract()
            
        text = soup.get_text(separator=' ')
        # INCREASED LIMIT: 50k chars for broader news coverage
        return ' '.join(text.split())[:50000] 
    except Exception as e:
        print(f"Error: {e}")
        return ""

def extract_structured_data(text):
    print("⏳ AI is extracting structured data...")
    
    prompt = f"""
    You are a data extraction engine. 
    Read the text below and extract the top 5 news stories.
    
    Return the output STRICTLY as a JSON Object with this format:
    {{
        "stories": [
            {{
                "headline": "Title of story",
                "category": "Politics/World/Tech/etc",
                "summary": "One sentence summary",
                "urgency": "High/Medium/Low"
            }}
        ]
    }}
    
    Do not output any markdown code blocks, just the raw JSON string.
    
    TEXT DATA:
    {text}
    """
    
    # UPDATED: Using Llama 3.1 + 16k Context
    response = ollama.chat(
        model='llama3.1', 
        messages=[{'role': 'user', 'content': prompt}],
        options={'num_ctx': 16384}
    )
    
    return response['message']['content']

def main():
    print(f"🌍 Scraping {URL}...")
    raw_text = fetch_clean_text(URL)
    
    if not raw_text:
        return

    json_string = extract_structured_data(raw_text)
    json_string = json_string.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(json_string)
        
        # Relative path fix (already applied previously, keeping it safe)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(script_dir, f"news_{datetime.now().strftime('%Y%m%d')}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        print(f"\n✅ Success! Data saved to: {filename}")
        print("--- Preview ---")
        print(json.dumps(data, indent=2))
        
    except json.JSONDecodeError:
        print("❌ The AI failed to produce valid JSON. Here is what it wrote:")
        print(json_string)

if __name__ == "__main__":
    main()