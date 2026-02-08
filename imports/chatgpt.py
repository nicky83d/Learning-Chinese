import os
from openai import OpenAI
from plaympg import playFile



import requests

def ask_chatgpt(prompt):
    
    playFile("resources/questions/okletmecheck")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": "gpt-4",  # You can replace this with other models like 'text-davinci-003' or 'text-codex-002'
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Error: " + response.text

# Example usage
#prompt = "What is the meaning of life?"
#response = ask_chatgpt(prompt)
#print(response)
