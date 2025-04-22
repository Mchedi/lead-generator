import requests
from config import GROQ_API_KEY, GROQ_CHAT_URL, GROQ_MODEL

def chat_with_groq(messages):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        response = requests.post(GROQ_CHAT_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return "I couldn't process that request. Please try again."
    except requests.exceptions.RequestException as e:
        print(f"API Error: {str(e)}")
        return "I'm having trouble connecting to the AI service. Please try again later."
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return "An unexpected error occurred. Please try again."