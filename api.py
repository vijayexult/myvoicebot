# api.py

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import websockets
import asyncio
import os
import logging

app = FastAPI()

# Path to save audio files
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

# Define the request model for sending voice input as a file
class VoiceRequest(BaseModel):
    file: UploadFile

# Define the WebSocket server details
WS_SERVER_URL = "ws://localhost:8765"

async def send_audio_to_websocket(audio_path: str):
    """Send audio to the WebSocket server and receive the response."""
    try:
        async with websockets.connect(WS_SERVER_URL) as websocket:
            # Read the audio file and send it to the WebSocket server
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                await websocket.send(audio_data)
                logging.info("Audio data sent to WebSocket server.")

            # Receive the response from the WebSocket server
            response_data = await websocket.recv()

            # Save the response audio file
            output_audio_path = os.path.join(AUDIO_DIR, "response_audio.mp3")
            with open(output_audio_path, 'wb') as f:
                f.write(response_data)
                logging.info("Response audio saved.")

            return output_audio_path
    except Exception as e:
        logging.error(f"WebSocket communication failed: {str(e)}")
        raise HTTPException(status_code=500, detail="WebSocket communication error.")

@app.post("/voice-to-text/")
async def process_voice(file: UploadFile = File(...)):
    """API endpoint to process voice input and return audio response."""
    try:
        # Save the received audio file locally
        input_audio_path = os.path.join(AUDIO_DIR, file.filename)
        with open(input_audio_path, 'wb') as audio_file:
            audio_file.write(file.file.read())
            logging.info(f"Audio file saved: {input_audio_path}")

        # Send the audio file to WebSocket and get the response
        response_audio_path = await send_audio_to_websocket(input_audio_path)

        # Return the audio response as a file download
        return FileResponse(response_audio_path, media_type="audio/mp3")
    except Exception as e:
        logging.error(f"Failed to process voice: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing voice input.")

@app.get("/")
def read_root():
    return {"message": "Voice Assistant API is running"}
