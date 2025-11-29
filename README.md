# 🕵️ AI Research Agent

A local AI-powered research suite that scrapes websites and uses **Ollama** (Llama 3.2) to summarize content, chat with pages, and extract structured data.

## 📂 Project Structure

* **`app.py`**: The main **Streamlit** web application. Provides a GUI to load a URL and chat with its content.
* **`web_chat_ai.py`**: A command-line interface (CLI) tool to chat with a website directly in your terminal.
* **`web_summarizer.py`**: A CLI tool that generates a bullet-point summary of any URL.
* **`news_to_json.py`**: An automated scraper that fetches top stories from NPR and saves them as a structured JSON file.

## 🚀 Prerequisites

1.  **Python 3.8+**
2.  **Ollama**: This project runs on local LLMs. You must have Ollama installed and running.
    * [Download Ollama](https://ollama.com/download)
    * Pull the required model:
        ```bash
        ollama pull llama3.2
        ```

## 🛠️ Installation

1.  **Clone or Open the Project**
    Navigate to your project folder in the terminal.

2.  **Set up the Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## 💻 Usage

### 1. Web Interface (Best Experience)
Launches the full graphical interface in your browser.
```bash
streamlit run app.py
```

### 2. Command Line Tools
Summarize a Website:
```bash
python web_summarizer.py [https://example.com](https://example.com)
```

### 3. Chat with a Website (Terminal Mode):
```bash
python web_chat_ai.py [https://example.com](https://example.com)
```

### 4. Extract News Data:
```bash
python news_to_json.py
```
(Note: This script currently targets npr.org by default and saves a JSON file to your D: drive project folder. You may want to edit the save path in the script.)

# 📝 Configuration
Model: The scripts use llama3.2 by default. You can change this to mistral or gemma by editing the model='...' line in the python files.

