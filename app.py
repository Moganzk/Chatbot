from flask import Flask, render_template, request, jsonify, session, send_file
import requests
import os
import json
import random
from dotenv import load_dotenv
from datetime import timedelta, datetime
from googletrans import Translator
import speech_recognition as sr
from gtts import gTTS
import pygame
import io
import PyPDF2
from io import BytesIO
import pytemperature  # For weather conversions

# Initialize app
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.permanent_session_lifetime = timedelta(hours=2)

# =====================
# KNOWLEDGE BASES
# =====================
with open('intents.json') as f:
    intents = json.load(f)
    
with open('agriculture_kb.json') as f:
    agri_knowledge = json.load(f)
    
with open('farming_manuals.json') as f:
    manuals = json.load(f)
    
with open('market_prices.json') as f:  # New: Crop prices
    market_data = json.load(f)

# =====================
# SERVICE INITIALIZATION
# =====================
translator = Translator()
recognizer = sr.Recognizer()
pygame.mixer.init()

# =====================
# CORE FUNCTIONALITIES
# =====================

# 1. STYLE MANAGEMENT (Gen-Z/Farmer)
STYLES = {
    "professional": {
        "error": "Apologies for the inconvenience. Please try again later.",
        "temp": 0.3
    },
    "genz": {
        "error": "Yo my bad 💀 Try again?",
        "temp": 0.7
    }
}

def detect_style(text):
    farmer_kws = ["crop", "soil", "harvest", "fertilizer", "livestock"]
    return "professional" if any(kw in text.lower() for kw in farmer_kws) else "genz"

# 2. LOCAL KNOWLEDGE QUERY
def get_local_response(query):
    # Check basic intents
    for intent in intents['intents']:
        if any(query.lower() == p.lower() for p in intent['patterns']):
            return random.choice(intent['responses'])
    
    # Check agriculture KB
    for item in agri_knowledge:
        if any(kw in query.lower() for kw in item['keywords']):
            return item['response']
    return None

# 3. WEATHER SERVICE (OpenWeatherMap)
def get_weather(location):
    try:
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={location}"
            f"&appid={os.getenv('WEATHER_API_KEY')}&units=metric"
        )
        data = response.json()
        return (
            f"📍 {location}\n"
            f"🌡️ Temp: {data['main']['temp']}°C (Feels like {data['main']['feels_like']}°C)\n"
            f"☁️ Conditions: {data['weather'][0]['description']}\n"
            f"💧 Humidity: {data['main']['humidity']}%\n"
            f"🌬️ Wind: {data['wind']['speed']} m/s"
        )
    except Exception as e:
        print(f"Weather error: {e}")
        return "Couldn't fetch weather data"

# 4. MARKET PRICES
def get_market_prices(crop=None):
    if crop:
        return next((item for item in market_data if crop.lower() in item['name'].lower()), None)
    return market_data[:5]  # Return top 5 by default

# 5. PDF MANUALS
def search_manuals(query):
    results = []
    for manual in manuals:
        if any(kw in query.lower() for kw in manual['keywords']):
            with open(manual['path'], 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                preview = pdf.pages[0].extract_text()[:150] + "..."
            results.append({
                "id": manual['id'],
                "title": manual['title'],
                "preview": preview
            })
    return results

# 6. VOICE PROCESSING
def process_voice(audio_file):
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            return recognizer.recognize_google(audio)
    except Exception as e:
        print(f"Voice error: {e}")
        return None

# 7. TRANSLATION SYSTEM
def translate_text(text, target_lang='en'):
    try:
        return translator.translate(text, dest=target_lang).text
    except:
        return text

# 8. TEXT-TO-SPEECH
def text_to_speech(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        print(f"TTS error: {e}")
        return None

# =====================
# ROUTES
# =====================

@app.route('/')
def home():
    session.clear()
    session['conversation'] = []
    session['language'] = 'en'
    return render_template('index.html')

@app.route('/get', methods=['POST'])
def chat():
    # Get input
    user_input = request.form.get('msg', "").strip()
    voice_file = request.files.get('voice')
    location = request.form.get('location', "")
    crop_query = request.form.get('crop', "")
    
    # Process voice
    if voice_file and not user_input:
        user_input = process_voice(voice_file) or ""
    
    # Detect response style
    style = detect_style(user_input)
    lang = session.get('language', 'en')
    
    # Special Commands
    if "weather" in user_input.lower() and location:
        weather_report = get_weather(location)
        return jsonify({
            "type": "weather",
            "response": translate_text(weather_report, lang),
            "style": style
        })
    
    if "price" in user_input.lower() or "market" in user_input.lower():
        prices = get_market_prices(crop_query)
        return jsonify({
            "type": "market",
            "response": translate_text(format_prices(prices), lang),
            "style": style
        })
    
    if "manual" in user_input.lower():
        found_manuals = search_manuals(user_input)
        return jsonify({
            "type": "manuals",
            "manuals": [{
                **manual,
                "title": translate_text(manual['title'], lang)
            } for manual in found_manuals],
            "style": style
        })
    
    # Local knowledge check
    local_reply = get_local_response(user_input)
    if local_reply:
        session['conversation'].append({"role": "user", "content": user_input})
        session['conversation'].append({"role": "assistant", "content": local_reply})
        return format_response(local_reply, style, lang)
    
    # Groq API call
    try:
        headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}
        messages = [
            {"role": "system", "content": f"Respond in {style} style"},
            *session['conversation'][-3:],
            {"role": "user", "content": user_input}
        ]
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json={
                "model": "llama3-70b-8192",
                "messages": messages,
                "temperature": STYLES[style]["temp"]
            },
            timeout=10
        )
        
        bot_reply = response.json()["choices"][0]["message"]["content"]
        session['conversation'].append({"role": "assistant", "content": bot_reply})
        return format_response(bot_reply, style, lang)
    
    except Exception as e:
        print(f"Groq error: {e}")
        return format_response(STYLES[style]["error"], style, lang)

def format_response(text, style, lang):
    translated = translate_text(text, lang)
    audio = None
    
    if request.args.get('voice') == 'true':
        audio = text_to_speech(translated, lang)
        if audio:
            return send_file(audio, mimetype='audio/mpeg')
    
    return jsonify({
        "type": "text",
        "response": translated,
        "style": style
    })

@app.route('/get_manual/<manual_id>')
def download_manual(manual_id):
    manual = next(m for m in manuals if m['id'] == manual_id)
    return send_file(manual['path'], as_attachment=True)

@app.route('/set_language', methods=['POST'])
def set_language():
    session['language'] = request.json.get('lang', 'en')
    return jsonify({"status": "success"})

# =====================
# UTILITIES
# =====================
def format_prices(prices):
    if isinstance(prices, list):
        return "\n".join([f"📊 {p['name']}: ${p['price']}/kg" for p in prices])
    elif prices:
        return f"📊 {prices['name']}: ${prices['price']}/kg (📍 {prices['region']})"
    return "No price data found"

# =====================
# RUN APP
# =====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)