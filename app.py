import os
import io
import uuid
import asyncio
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import edge_tts

app = Flask(__name__)
CORS(app)

# Voice mappings for male/female
VOICE_MAPPING = {
    'en': {
        'male': 'en-US-BrandonNeural',
        'female': 'en-US-JennyNeural'
    },
    'fr': {
        'male': 'fr-FR-HenriNeural',
        'female': 'fr-FR-DeniseNeural'
    },
}

def wrap_text_in_ssml(text):
    """Wrap text in proper SSML format"""
    return f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">{text}</speak>'

def has_ssml_tags(text):
    """Check if text contains SSML tags"""
    ssml_tags = ['<break', '<emphasis', '<prosody', '<say-as', '<phoneme', '<sub']
    return any(tag in text.lower() for tag in ssml_tags)

async def generate_speech(text, voice, rate="+0%"):
    """Generate speech using edge-tts"""
    if has_ssml_tags(text):
        text = wrap_text_in_ssml(text)
        
    
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio_data = b""
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    
    return audio_data

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "Edge-TTS"})

@app.route("/tts", methods=["POST"])
def text_to_speech():
    """Convert text to speech using Microsoft Edge TTS"""
    try:
        # Get JSON data
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
        
        text = data['text'].strip()
        language = data.get('language', 'en')
        gender = data.get('gender', 'male')  # 'male' or 'female'
        slow = data.get('slow', False)
        
        # Validate input
        if not text:
            return jsonify({"error": "Empty text"}), 400
        if len(text) > 5000:
            return jsonify({"error": "Text too long (max 5000 chars)"}), 400
        
        # Get voice for language and gender
        if language not in VOICE_MAPPING:
            return jsonify({"error": f"Language {language} not supported"}), 400
        
        if gender not in VOICE_MAPPING[language]:
            return jsonify({"error": f"Gender {gender} not available for {language}"}), 400
        
        voice = VOICE_MAPPING[language][gender]
        
        # Adjust rate for slow speech
        if slow:
            rate = "-15%"  # slower
        else:
            rate = "+0%"   # Normal speed
        
        # Generate speech (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data = loop.run_until_complete(generate_speech(text, voice, rate))
        loop.close()
        
        # Create audio buffer
        audio_buffer = io.BytesIO(audio_data)
        audio_buffer.seek(0)
        
        speed_label = "slow" if slow else "normal"
        filename = f"speech_{gender}_{speed_label}_{uuid.uuid4().hex[:8]}.mp3"
        
        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/voices", methods=["GET"])
def get_voices():
    """Get available voices"""
    return jsonify({
        "voices": VOICE_MAPPING,
        "supported_genders": ["male", "female"],
        "supported_languages": list(VOICE_MAPPING.keys()),
        "speed_options": ["normal", "slow"]
    })

@app.route("/languages", methods=["GET"])
def get_languages():
    """Get supported languages"""
    languages = {
        'en': 'English',
        'fr': 'French'
    }
    return jsonify(languages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)