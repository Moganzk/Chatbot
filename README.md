# Mogan Chatbot (Groq Edition)

Now powered by **Llama 3 70B** via Groq's ultra-fast API!

## Features
- **Conversational AI** with Llama 3 70B (Groq)
- **File uploads:** Supports text, PDF, DOCX, PPTX, images (with OCR), code, and more
- **Audio uploads:** Voice-to-text support
- **Image OCR:** Extracts text from images using pytesseract
- **Drag & drop** and multi-file upload
- **Responsive UI** for mobile, tablet, and desktop
- **Hybrid mode:** Uses Groq for conversation, local fallback for classic intents

---

## Setup

1. **Get a free API key** at [Groq Cloud](https://console.groq.com/)
2. **Create a `.env` file** in your project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   FLASK_SECRET_KEY=your_flask_secret_key_here
   FLASK_ENV=development
   OPENAI_API_KEY=your_openai_api_key_here  # Optional, for OCR or translation
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install pillow pytesseract python-docx python-pptx
   ```
   - For OCR, [install Tesseract](https://github.com/tesseract-ocr/tesseract) on your system.

---

## How to Run

1. Start the server:
   ```bash
   python app.py
   ```
2. Open [http://localhost:5000](http://localhost:5000) in your browser.
3. Chat, upload files, or drag & drop images, docs, or audio!

---

## Key Features & Improvements

- **Endpoint fixed:** Frontend and backend both use `/get`
- **Form data:** Frontend sends `msg=` and files as form data
- **Error handling:** Friendly messages for unsupported files or OCR failures
- **File preview:** See attached files and images before sending, with option to remove
- **Multiple file upload:** Attach and send several files at once
- **Image analysis:** Extracts text from images (if possible), otherwise gives a helpful fallback message

---

## Supported File Types

- Text: `.txt`, `.md`, `.csv`, `.json`
- Documents: `.pdf`, `.docx`, `.pptx`
- Code: `.py`, `.js`, `.java`, `.c`, `.cpp`, `.html`
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp` (with OCR)
- Audio: `.mp3`, `.wav`, `.ogg`, `.m4a`

---

## Next Steps / Ideas

- Add **admin dashboard** for monitoring
- Deploy to **Railway**, **Vercel**, or your favorite cloud
- Add **user authentication** or chat history

---

## Troubleshooting

- **OCR not working?**  
  Make sure Tesseract is installed and in your system PATH.
- **API errors?**  
  Double-check your `.env` keys and network connection.
- **File not processed?**  
  Only supported file types are handled; others are skipped with a friendly message.

---

Want more features or help deploying?  
**Just ask! 🚀**