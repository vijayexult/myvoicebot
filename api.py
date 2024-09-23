from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio
import logging
from voice_assistant.transcription import transcribe_audio
from voice_assistant.response_generation import generate_response
from voice_assistant.text_to_speech import text_to_speech
from voice_assistant.utils import delete_file
from voice_assistant.config import Config
from voice_assistant.api_key_manager import get_transcription_api_key, get_response_api_key, get_tts_api_key

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Voice Assistant API! Use the /voice endpoint to interact."}

@app.post("/voice")
async def process_voice(file: UploadFile = File(...), text: str = None):
    audio_bytes = await file.read()
    audio_file = 'received_audio.wav'
    
    # Save the audio data to a file
    with open(audio_file, 'wb') as f:
        f.write(audio_bytes)
    
    logging.info(f"Audio file saved as {audio_file}")
    logging.info(f"Received audio data size: {len(audio_bytes)} bytes")
    
    # Transcribe audio to text
    transcription_api_key = get_transcription_api_key()
    try:
        user_input = await asyncio.to_thread(transcribe_audio, Config.TRANSCRIPTION_MODEL, transcription_api_key, audio_file, Config.LOCAL_MODEL_PATH)
        logging.info(f"Transcribed text: {user_input}")
    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        return {"error": "Transcription failed. Please check the audio file."}

    if not user_input:
        return {"error": "Transcription failed. No audio understood."}

    # If user provided text, append to conversation
    if text:
        user_input = text  # Use the provided text instead of transcription if available
    
    # Generate response from the assistant
    response_api_key = get_response_api_key()
    chat_history = [{"role": "user", "content": user_input}]
    try:
        response_text = await asyncio.to_thread(generate_response, Config.RESPONSE_MODEL, response_api_key, chat_history, Config.LOCAL_MODEL_PATH)
        logging.info(f"Assistant response: {response_text}")
    except Exception as e:
        logging.error(f"Response generation failed: {e}")
        return {"error": "Response generation failed."}

    # Convert response text to speech
    output_file = 'output.wav'
    tts_api_key = get_tts_api_key()
    try:
        await asyncio.to_thread(text_to_speech, Config.TTS_MODEL, tts_api_key, response_text, output_file, Config.LOCAL_MODEL_PATH)
        logging.info(f"TTS output saved as {output_file}")
    except Exception as e:
        logging.error(f"TTS conversion failed: {e}")
        return {"error": "Text-to-speech conversion failed."}

    # Read the output file and return as a response
    def iter_file():
        with open(output_file, "rb") as f:
            yield from f
    
    response = StreamingResponse(iter_file(), media_type="audio/wav")
    
    # Clean up
    delete_file(audio_file)
    delete_file(output_file)
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
