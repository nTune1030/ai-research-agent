import json
import requests
from bs4 import BeautifulSoup
import ollama
from datetime import datetime

# URL to scrape
URL = "https://www.npr.org/"

def fetch_clean_text(url):
    """(Same scraping logic as before)"""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Aggressive cleaning to fit more content in context
        for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
            tag.extract()
            
        text = soup.get_text(separator=' ')
        # Collapse whitespace
        return ' '.join(text.split())[:15000] 
    except Exception as e:
        print(f"Error: {e}")
        return ""

def extract_structured_data(text):
    print("⏳ AI is extracting structured data...")
    
    # The Prompt: We explicitly demand a JSON array
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
    
    response = ollama.chat(model='llama3.2', messages=[
        {'role': 'user', 'content': prompt}
    ])
    
    return response['message']['content']

def main():
    print(f"🌍 Scraping {URL}...")
    raw_text = fetch_clean_text(URL)
    
    if not raw_text:
        return

    # Get the raw string from AI
    json_string = extract_structured_data(raw_text)
    
    # Clean up AI output (sometimes it adds ```json fences)
    json_string = json_string.replace("```json", "").replace("```", "").strip()

    try:
        # Parse it into a real Python Dictionary
        data = json.loads(json_string)
        
        # Save to your D: drive
        filename = f"D:/AI_Workstation/projects/news_{datetime.now().strftime('%Y%m%d')}.json"
        
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