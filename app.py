import os
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
import requests
import json
import random
from dotenv import load_dotenv
from datetime import timedelta, datetime
import speech_recognition as sr
from gtts import gTTS
import pygame
import io
import PyPDF2
from io import BytesIO
import pytemperature  # For weather conversions
import docx
from pptx import Presentation
import csv
import openai
from PIL import Image
import base64
import pytesseract
import time
import code_generator  # Import the code generator module
import document_generator  # Import the document generator module
import re  # For regex pattern matching
from conversation_memory import memory  # Import the conversation memory module
import uuid  # For generating session IDs

# Initialize app
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.permanent_session_lifetime = timedelta(hours=2)
CORS(app)

# =====================
# KNOWLEDGE BASES
# =====================
def safe_load_json(filename, default):
    try:
        with open(filename) as f:
            data = json.load(f)
            return data if data else default
    except Exception:
        return default

intents = safe_load_json('intents.json', {"intents": []})
agri_knowledge = safe_load_json('agriculture_kb.json', [])
manuals = safe_load_json('farming_manuals.json', [])
market_data = safe_load_json('market_prices.json', [])

# =====================
# SERVICE INITIALIZATION
# =====================

recognizer = sr.Recognizer()
try:
    pygame.mixer.init()
except Exception as e:
    print("Audio init failed (likely no audio device on server):", e)

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

# 9. IMAGE ANALYSIS (OpenAI Vision API)
def analyze_image(file_storage):
    # Convert image to base64
    image = Image.open(file_storage)
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    # Call OpenAI Vision API (GPT-4o)
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes images and answers questions about them."},
            {"role": "user", "content": [
                {"type": "text", "text": "Describe this image and answer any question about it."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
            ]}
        ],
        max_tokens=400
    )
    return response.choices[0].message.content

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
def process_message():
    # Initialize conversation if needed
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    style = request.form.get('style', "Informative")
    lang = request.form.get('lang', "en")
    
    if style not in STYLES:
        style = "Informative"
    
    def format_response(text, style, lang):
        # Enhance formatting
        enhanced_text = enhance_response_formatting(text)
        
        # Translate if needed
        translated = translate_text(enhanced_text, lang)
        audio = None
        
        if request.args.get('voice') == 'true':
            audio = text_to_speech(translated, lang)
        
        return jsonify({
            "response": translated, 
            "audio": audio,
            "style": style
        })

    start = time.time()
    user_input = request.form.get('msg', "").strip()
    audio_files = [f for k, f in request.files.items() if k.startswith('voice')]
    doc_files = [f for k, f in request.files.items() if k.startswith('document')]
    location = request.form.get('location', "")
    crop_query = request.form.get('crop', "")
    # Get deep reasoning mode parameter (use 'false' as the default if not specified)
    deep_reasoning_param = request.form.get('deep_reasoning', 'false').lower() in ('true', 'yes', '1')

    # Add user message to conversation memory
    memory.add_message(session_id, 'user', user_input)

    # Check if this is a code-related request
    if user_input and code_generator.is_code_request(user_input):
        # Get conversation context for code generation
        context = memory.get_conversation_context(session_id, max_context_turns=3)
        
        # Generate code with context
        if context:
            # Add context to the query
            code_response = code_generator.generate_code(f"{context}\n\nCurrent request: {user_input}")
        else:
            code_response = code_generator.generate_code(user_input)
        
        # Add bot response to memory
        memory.add_message(session_id, 'bot', code_response)
        return jsonify({"response": code_response})
    
    # Check if this is a document generation request
    if user_input and document_generator.is_document_request(user_input):
        # Get conversation context for document generation
        context = memory.get_conversation_context(session_id, max_context_turns=3)
        
        # Generate document with context
        if context:
            # Add context to the query
            document_response = document_generator.generate_document(f"{context}\n\nCurrent request: {user_input}")
        else:
            document_response = document_generator.generate_document(user_input)
        
        # Add bot response to memory
        memory.add_message(session_id, 'bot', document_response)
        return jsonify({"response": document_response})
    
    # Check if this is an educational/conceptual request
    is_educational = code_generator.is_educational_request(user_input)
    is_code_request = code_generator.is_code_request(user_input)
    print(f"Educational request: {is_educational}, Code request: {is_code_request}, Query: {user_input[:50]}...")

    # Process all audio files (concatenate recognized text)
    for audio_file in audio_files:
        voice_text = process_voice(audio_file)
        if voice_text:
            user_input += " " + voice_text

    skipped_files = []
    # Process all document files (concatenate extracted text)
    for doc_file in doc_files:
        filename = doc_file.filename.lower()
        text = ""
        try:
            # Limit file size
            MAX_FILE_SIZE_MB = 5
            if doc_file.content_length and doc_file.content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
                skipped_files.append(doc_file.filename + " (too large)")
                continue

            if filename.endswith('.txt'):
                doc_file.seek(0)
                text = doc_file.read().decode('utf-8')
            elif filename.endswith('.csv'):
                doc_file.seek(0)
                decoded = doc_file.read().decode('utf-8')
                reader = csv.reader(decoded.splitlines())
                for row in reader:
                    text += ', '.join(row) + '\n'
            # ...rest of your file types...
        except Exception as e:
            print(f"File error: {e}")
            continue
        user_input += " " + text[:1000]  # Limit each file's text
        doc_file.seek(0)

    # After processing, add to response if any skipped
    if skipped_files:
        skip_msg = f"Note: These files were not processed (unsupported type): {', '.join(skipped_files)}"
        user_input += " " + skip_msg

    # Limit total input length for LLM
    MAX_INPUT_LENGTH = 4000
    user_input = user_input[:MAX_INPUT_LENGTH]

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
        # Add bot response to memory
        memory.add_message(session_id, 'bot', local_reply)
        return format_response(local_reply, style, lang)

    # Groq API call (handles open-ended conversation)
    try:
        headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}
        
        # Get conversation history from memory
        conversation_history = memory.get_conversation_history(session_id)
        
        # Check if deep reasoning is needed (user toggle or auto-detect)
        use_deep_reasoning = deep_reasoning_param or needs_deep_reasoning(user_input)
        reasoning_mode = "Deep Reasoning" if use_deep_reasoning else "Standard"
        print(f"Using {reasoning_mode} mode for query: {user_input[:50]}...")
        
        # Enhanced system prompt with structured response guidelines and deep reasoning
        if is_educational:
            # Use educational-focused system prompt (no code bias)
            system_prompt = get_enhanced_system_prompt(use_deep_reasoning, deep_reasoning_param)
            system_prompt += """
            
EDUCATIONAL RESPONSE MODE:
The user is asking for conceptual or educational information. Provide clear explanations without code unless explicitly requested."""
        else:
            # Use general conversation system prompt
            system_prompt = f"""You are Mogan, a helpful, intelligent assistant capable of deep reasoning. 
Respond in {style} style and structure your responses clearly for readability.

"""
        
        # Add reasoning instructions based on detected complexity
        if use_deep_reasoning:
            system_prompt += """REASONING APPROACH (Use deep reasoning for this complex query):
- Break down this complex problem into clear logical components
- Use explicit step-by-step reasoning to work through each part
- Consider multiple perspectives and approaches
- Make your thought process completely explicit
- Identify and state key assumptions you're making
- Examine implications and potential edge cases
- For technical topics, apply first principles thinking
- Show detailed work for any mathematical or logical problems
- Present pros and cons of different solutions or viewpoints
- End with a clear, justified conclusion

Use dedicated sections for your reasoning process with headings like:
* "## Initial Analysis"
* "## Step-by-Step Reasoning"
* "## Alternative Perspectives" 
* "## Key Considerations"
* "## Conclusion"

"""
        else:
            system_prompt += """REASONING APPROACH:
- For questions requiring explanation, use clear logical reasoning
- Break down problems into manageable components when helpful
- Consider the most relevant perspectives or solution paths
- Make your reasoning process understandable
- Consider important assumptions and implications

"""
        
        # Add document formatting guidance
        system_prompt += """DOCUMENT CREATION:
When asked to create a document like a CV, resume, proposal, or report:
- Provide clear structure with appropriate sections
- Use professional language and formatting
- Include guidance on how to customize the document
- Follow standard conventions for the requested document type
- Add helpful tips for finalizing the document

"""
        
        # Add standard formatting instructions for all responses
        system_prompt += """RESPONSE FORMATTING:
- Use markdown formatting for better readability
- Organize complex responses with clear section headings using ## or ### markdown syntax
- For lists, use bullet points (•) or numbered lists when appropriate
- When explaining concepts, break them down into clear paragraphs
- When providing examples, clearly label them as examples
- For step-by-step instructions, number each step and be concise
- Use **bold** for emphasis on important points or keywords
- For tables, use proper markdown table formatting
- Keep your tone {style.lower()} as requested by the user

When answering questions about programming or technical topics:
- Begin with a brief summary of the solution
- Provide well-structured, properly indented code examples
- Add explanatory comments within code where helpful
- After code examples, explain key concepts or functions used
- Always suggest best practices or optimization tips when relevant

For factual information:
- Present key facts first, followed by supporting details
- Cite relevant information sources when available
- Distinguish between facts and opinions clearly

For complex topics:
- Start with a simple explanation, then progressively add complexity
- Use analogies or examples to clarify difficult concepts
- Break down multi-part answers into clearly labeled sections

Always maintain a helpful, informative tone while organizing information in an easily digestible format.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-16:],  # Use the last 16 messages from conversation memory
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
        
        # Add indicators for special modes
        if is_educational:
            bot_reply = f"📚 *Educational Response*\n\n{bot_reply}"
        
        # Add bot response to memory
        memory.add_message(session_id, 'bot', bot_reply)
        
        return format_response(bot_reply, style, lang)
    except Exception as e:
        print(f"Groq error: {e}")
        error_message = STYLES[style]["error"]
        memory.add_message(session_id, 'bot', error_message)
        return format_response(error_message, style, lang)

@app.route('/get_manual/<manual_id>')
def download_manual(manual_id):
    manual = next((m for m in manuals if m['id'] == manual_id), None)
    if not manual or not os.path.exists(manual['path']):
        return "Manual not found.", 404
    return send_file(manual['path'], as_attachment=True)

@app.route('/set_language', methods=['POST'])
def set_language():
    session['language'] = request.json.get('lang', 'en')
    return jsonify({"status": "success"})

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.json
    feedback = data.get('feedback')
    msg_id = data.get('msg_id')
    # Save feedback to a file (or database)
    with open('feedback_log.jsonl', 'a') as f:
        f.write(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": feedback,
            "msg_id": msg_id,
            "session": session.get('conversation', [])
        }) + "\n")
    return jsonify({"status": "ok"})

@app.route('/clear_history', methods=['POST'])
def clear_conversation_history():
    """Clear the conversation history for the current session"""
    if 'session_id' in session:
        memory.clear_conversation(session['session_id'])
        return jsonify({"status": "success", "message": "Conversation history cleared"})
    return jsonify({"status": "error", "message": "No active session found"})

# =====================
# UTILITIES
# =====================
def format_prices(prices):
    if isinstance(prices, list):
        return "\n".join([f"📊 {p['name']}: ${p['price']}/kg" for p in prices])
    elif prices:
        return f"📊 {prices['name']}: ${prices['price']}/kg (📍 {prices['region']})"
    return "No price data found"

def enhance_response_formatting(text):
    """
    Enhance the response text with better formatting for certain content types
    and improve reasoning structure
    """
    # Add reasoning structure if it appears to be a complex question without structure
    if len(text) > 500 and not re.search(r'#{2,3}\s+\w+', text) and (
        re.search(r'(why|how|explain|analyze|compare|evaluate|reason|think|consider)', text.lower())
    ):
        # This seems like a complex answer that would benefit from structure
        parts = text.split('\n\n')
        
        if len(parts) >= 3:  # If we have enough content to structure
            # First paragraph as introduction
            structured_text = parts[0] + "\n\n"
            
            # Add analysis section
            structured_text += "## Analysis\n\n" + parts[1] + "\n\n"
            
            # Middle parts as step-by-step reasoning
            structured_text += "## Step-by-Step Reasoning\n\n"
            for i, part in enumerate(parts[2:-1], start=1):
                if len(part.strip()) > 0:
                    structured_text += f"### Step {i}: {part.strip()[:40].split('.')[0]}\n\n"
                    structured_text += part + "\n\n"
            
            # Last part as conclusion
            structured_text += "## Conclusion\n\n" + parts[-1]
            
            text = structured_text
    
    # Convert simple lists (like "1. item") to proper markdown lists
    text = re.sub(r'(?m)^(\d+)\.\s+(.+)$', r'\1. \2', text)
    
    # Make sure headers have proper spacing
    text = re.sub(r'(?m)^(#{1,6})([^#\s].+)$', r'\1 \2', text)
    
    # Convert simple tables to markdown tables if they're not already
    # This is a simplistic approach - complex tables will need proper formatting already
    table_pattern = r'(?m)^([^|].+?\|.+[^|]?)$'
    if re.search(table_pattern, text) and '---' not in text:
        lines = text.split('\n')
        table_lines = []
        in_table = False
        header_added = False
        
        for i, line in enumerate(lines):
            if re.match(table_pattern, line) and not in_table:
                in_table = True
                table_lines.append(line)
                if not header_added:
                    # Count pipes and create header separator
                    pipe_count = line.count('|')
                    table_lines.append('|' + '---|' * pipe_count)
                    header_added = True
            elif re.match(table_pattern, line) and in_table:
                table_lines.append(line)
            elif in_table:
                in_table = False
                header_added = False
                table_lines.append(line)
            else:
                table_lines.append(line)
        
        text = '\n'.join(table_lines)
    
    # Make sure code blocks are properly formatted
    text = re.sub(r'```(\w*)\s*\n', r'```\1\n', text)
    
    # Ensure links are properly formatted
    text = re.sub(r'\[([^\]]+)\]\s*\(([^)]+)\)', r'[\1](\2)', text)
    
    # Ensure proper formatting for pros and cons if present
    if re.search(r'\b(pros|cons|advantages|disadvantages|benefits|drawbacks)\b', text.lower()):
        text = re.sub(r'(?i)(\n|^)pros[:\s]*', r'\1### Pros\n\n', text)
        text = re.sub(r'(?i)(\n|^)cons[:\s]*', r'\1### Cons\n\n', text)
        text = re.sub(r'(?i)(\n|^)advantages[:\s]*', r'\1### Advantages\n\n', text)
        text = re.sub(r'(?i)(\n|^)disadvantages[:\s]*', r'\1### Disadvantages\n\n', text)
        text = re.sub(r'(?i)(\n|^)benefits[:\s]*', r'\1### Benefits\n\n', text)
        text = re.sub(r'(?i)(\n|^)drawbacks[:\s]*', r'\1### Drawbacks\n\n', text)
    
    return text

def needs_deep_reasoning(query):
    """
    Detect if a query would benefit from deeper reasoning based on keywords and complexity
    """
    # Keywords that suggest analytical thinking is needed
    reasoning_keywords = [
        "why", "how does", "explain", "analyze", "compare", "evaluate", 
        "reason", "think", "consider", "implications", "effects", 
        "consequences", "causes", "differences", "similarities", "relationship",
        "mechanism", "process", "theory", "concept", "perspective", "trade-offs",
        "approach", "methodology", "pros and cons", "advantages", "disadvantages",
        "design decision", "architecture", "framework", "strategy", "debate",
        "opinion", "viewpoint", "stance", "argument", "critique", "review",
        "assessment", "hypothesis", "prediction", "forecast", "impact", "outcome"
    ]
    
    # Technical topics that often benefit from step-by-step reasoning
    technical_keywords = [
        "algorithm", "system", "architecture", "protocol", "framework", 
        "design pattern", "optimization", "complexity", "scale", "performance",
        "efficiency", "reliability", "security", "consistency", "concurrency",
        "distributed", "parallelism", "asynchronous", "synchronization",
        "engineering", "scientific", "mathematical", "statistical", "economic",
        "cryptographic", "blockchain", "consensus", "policy", "regulation"
    ]
    
    query_lower = query.lower()
    
    # Check for reasoning keywords
    reasoning_score = sum(1 for keyword in reasoning_keywords if keyword in query_lower)
    
    # Check for technical topics
    technical_score = sum(1 for keyword in technical_keywords if keyword in query_lower)
    
    # Check for complex question structures
    question_complexity = 0
    if "?" in query:
        question_complexity += 1
    if len(query.split()) > 15:  # Longer questions tend to be more complex
        question_complexity += 1
    if any(connector in query_lower for connector in ["because", "therefore", "however", "although", "despite", "while", "unless"]):
        question_complexity += 2
    
    # Calculate total score
    total_score = reasoning_score + technical_score + question_complexity
    
    return total_score >= 2  # Threshold for deep reasoning

def needs_document_formatting(query):
    """
    Detect if a document request needs special formatting attention
    """
    # Document formatting keywords and phrases
    formatting_keywords = [
        "professional", "formal", "template", "standard format", "proper format",
        "industry standard", "well-formatted", "layout", "structure", "sections",
        "organized", "official", "conventional", "proper structure", "best practice",
        "formatting", "styled", "clean design", "presentable"
    ]
    
    query_lower = query.lower()
    
    # Check for formatting keywords
    formatting_score = sum(1 for keyword in formatting_keywords if keyword in query_lower)
    
    # Check for document type indicators
    document_types = ["resume", "cv", "cover letter", "proposal", "business plan", 
                      "report", "memo", "presentation", "white paper", "press release",
                      "application", "letter", "thesis", "dissertation", "essay"]
                      
    doc_type_mentioned = any(doc_type in query_lower for doc_type in document_types)
    
    # Determine if document formatting is needed
    return (formatting_score >= 2) or (formatting_score >= 1 and doc_type_mentioned)

def get_enhanced_system_prompt(use_deep_reasoning=False, user_requested_deep_reasoning=False):
    """Enhanced system prompt with better code detection logic"""
    
    base_prompt = """You are Mogan, a helpful and intelligent AI assistant. Your primary goal is to provide clear, informative, and engaging responses to user questions.

IMPORTANT CODE GENERATION RULES:
- ONLY provide code snippets when the user EXPLICITLY asks for code or mentions specific programming implementation requests
- If the user asks general questions, educational questions, or requests for lists/explanations, respond with clear text - NO CODE
- When in doubt, provide natural language explanations and ask clarifying questions
- Code should only be generated for implementation requests, not conceptual explanations

Examples of when to provide code:
✅ "write a function to sort an array in Python"
✅ "show me how to implement bubble sort in Java"
✅ "create a React component for a login form"
✅ "give me code for connecting to a database"

Examples of when NOT to provide code:
❌ "explain how bubble sort works" → Provide conceptual explanation
❌ "what are the benefits of Python?" → Provide text explanation  
❌ "give me 10 questions about networking" → Provide plain text list
❌ "how does machine learning work?" → Provide educational explanation

RESPONSE GUIDELINES:
- Structure your responses with clear headings and bullet points when appropriate
- Use markdown formatting for better readability
- Be conversational and engaging
- Ask follow-up questions when clarification is needed
- Provide examples and analogies to explain complex concepts
- Keep responses focused and relevant to the user's question"""

    if use_deep_reasoning or user_requested_deep_reasoning:
        base_prompt += """

DEEP REASONING MODE ACTIVATED:
When deep reasoning is requested, provide thorough analysis with:
- Comprehensive problem breakdown
- Multiple perspectives and approaches
- Detailed explanations with supporting evidence
- Step-by-step reasoning process
- Potential implications and considerations
- Well-structured sections with clear headings"""

    return base_prompt

# =====================
# RUN APP
# =====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)