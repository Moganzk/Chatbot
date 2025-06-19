import json
import random
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ai-models', 'chatbot')))
#from core import chatbot_response

# Load knowledge bases (adjust paths as needed)
with open(os.path.join(os.path.dirname(__file__), 'intents.json')) as f:
    intents = json.load(f)
with open(os.path.join(os.path.dirname(__file__), 'agriculture_kb.json')) as f:
    agri_knowledge = json.load(f)

def get_local_response(query):
    for intent in intents['intents']:
        if any(query.lower() == p.lower() for p in intent['patterns']):
            return random.choice(intent['responses'])
    for item in agri_knowledge:
        if any(kw in query.lower() for kw in item['keywords']):
            return item['response']
    return None

def chatbot_response(user_input):
    # Try local knowledge base first
    local_reply = get_local_response(user_input)
    if local_reply:
        return local_reply
    # Fallback: generic response
    return "Sorry, I don't have an answer for that yet."