import os
import io
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from app import gTTS

app = Flask(__name__)
CORS(app)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "gTTS"})

@app.route("/tts", methods=["POST"])
def text_to_speech():
    """Convert text to speech using Google TTS"""
    try:
        # Get JSON data
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
        
        text = data['text'].strip()
        language = data.get('language', 'en')
        slow = data.get('slow', False)
        
        # Validate input
        if not text:
            return jsonify({"error": "Empty text"}), 400
        if len(text) > 5000:
            return jsonify({"error": "Text too long (max 5000 chars)"}), 400
        
        # Generate speech
        tts = gTTS(text=text, lang=language, slow=slow)
        
        # Save to memory buffer (no file system needed)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        filename = f"speech_{uuid.uuid4().hex[:8]}.mp3"
        
        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/languages", methods=["GET"])
def get_languages():
    """Get supported languages"""
    # Most common languages supported by gTTS
    languages = {
        'en': 'English',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish',
        'pl': 'Polish',
        'tr': 'Turkish',
        'th': 'Thai',
        'vi': 'Vietnamese'
    }
    return jsonify(languages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)