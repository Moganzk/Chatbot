from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load local intents
with open('intents.json') as f:
    intents = json.load(f)

def get_local_response(user_message):
    """Check if message matches any local intent patterns"""
    for intent in intents['intents']:
        if any(user_message.lower() == pattern.lower() for pattern in intent['patterns']):
            return random.choice(intent['responses'])
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get', methods=['POST'])
def get_bot_response():
    user_message = request.form.get('msg')
    if not user_message:
        return jsonify({"response": "You sent an empty message 🤨"})

    # 1. First try local intents
    local_reply = get_local_response(user_message)
    if local_reply:
        return jsonify({"response": local_reply})

    # 2. Fallback to Groq API
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10  # 10-second timeout
        )
        response.raise_for_status()  # Raise HTTP errors
        
        return jsonify({
            "response": response.json()["choices"][0]["message"]["content"]
        })

    except requests.exceptions.RequestException as e:
        error_msg = f"API Error: {str(e)}" if os.getenv('FLASK_ENV') == 'development' else "My brain crashed 💀"
        return jsonify({"response": error_msg})

if __name__ == '__main__':
    app.run(debug=True)