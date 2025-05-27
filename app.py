import os
import json
import random
import pickle
import numpy as np
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai
import datetime
import re

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Load intents and model for fallback/local tasks
with open('intents.json') as f:
    intents = json.load(f)

with open('chatbot_model.pkl', 'rb') as f:
    model = pickle.load(f)

def handle_local_tasks(user_input):
    # Example: tell the time
    if "time" in user_input.lower():
        now = datetime.datetime.now().strftime("%H:%M")
        return f"The current time is {now}."
    # Math solver
    match = re.search(r'(\d+)\s*([\+\-\*/])\s*(\d+)', user_input)
    if match:
        a, op, b = match.groups()
        a, b = float(a), float(b)
        if op == '+':
            return f"{a} + {b} = {a + b}"
        elif op == '-':
            return f"{a} - {b} = {a - b}"
        elif op == '*':
            return f"{a} * {b} = {a * b}"
        elif op == '/':
            return f"{a} / {b} = {a / b if b != 0 else 'undefined (division by zero)'}"
    return None

def get_response(user_input):
    # First, check for local tasks
    local_response = handle_local_tasks(user_input)
    if local_response:
        return local_response

    # If user wants to google/search, return a Google link
    if "google" in user_input.lower() or "search" in user_input.lower():
        return f"🔍 <a href='https://www.google.com/search?q={user_input.replace(' ', '+')}' target='_blank'>Search on Google</a>"

    # Otherwise, use OpenAI for a smart response
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Mogan, a helpful, witty assistant."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI error:", e)  # Add this line
        # Fallback to classic intent-based response if OpenAI fails
        predicted_proba = model.predict_proba([user_input])[0]
        max_proba = np.max(predicted_proba)
        intent_tag = model.classes_[np.argmax(predicted_proba)]
        if max_proba < 0.2:
            return "Sorry, I don't understand. Can you rephrase?"
        for intent in intents['intents']:
            if intent['tag'] == intent_tag:
                return random.choice(intent['responses'])
        return "uhh... what?"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def chat():
    user_input = request.form["msg"]
    bot_response = get_response(user_input)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True)

