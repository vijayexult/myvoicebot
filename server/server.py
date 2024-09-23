import asyncio
import websockets
import logging
import os
from voice_assistant.transcription import transcribe_audio
from voice_assistant.response_generation import generate_response
from voice_assistant.text_to_speech import text_to_speech
from voice_assistant.utils import delete_file
from config.config import Config
from voice_assistant.api_key_manager import get_transcription_api_key, get_response_api_key, get_tts_api_key
import time  # For measuring response time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cache models (load once, reuse)
transcription_model = None
response_model = None
tts_model = None

async def process_audio(audio_file, chat_history):
    global transcription_model, response_model  # Use global cached models

    if not transcription_model:
        transcription_model = Config.TRANSCRIPTION_MODEL  # Load transcription model
    if not response_model:
        response_model = Config.RESPONSE_MODEL  # Load response model

    transcription_api_key = get_transcription_api_key()

    # Start timing for transcription
    transcription_start_time = time.perf_counter()
    
    # Run transcription asynchronously
    user_input_task = asyncio.to_thread(transcribe_audio, transcription_model, transcription_api_key, audio_file, Config.LOCAL_MODEL_PATH)
    user_input = await user_input_task
    
    transcription_end_time = time.perf_counter()
    transcription_time = transcription_end_time - transcription_start_time
    logging.info(f"Transcription took {transcription_time:.3f} seconds")

    if not user_input:
        logging.info("No transcription returned.")
        return None, None

    logging.info(f"User said: {user_input}")

    if "goodbye" in user_input.lower():
        return user_input, "Goodbye!"

    # Append user's input to chat history
    chat_history.append({"role": "user", "content": user_input})

    response_api_key = get_response_api_key()

    # Start timing for response generation (LLM)
    llm_start_time = time.perf_counter()

    # Generate a response asynchronously
    response_text_task = asyncio.to_thread(generate_response, response_model, response_api_key, chat_history, Config.LOCAL_MODEL_PATH)
    response_text = await response_text_task

    llm_end_time = time.perf_counter()
    llm_time = llm_end_time - llm_start_time
    logging.info(f"LLM response generation took {llm_time:.3f} seconds")

    logging.info(f"Assistant response: {response_text}")

    # Append assistant's response to chat history
    chat_history.append({"role": "assistant", "content": response_text})

    return user_input, response_text


async def handle_client(websocket, path):
    global tts_model  # Cache TTS model

    if not tts_model:
        tts_model = Config.TTS_MODEL  # Load TTS model once

    chat_history = [
        {"role": "system", "content": """You are a helpful Assistant called Verbi.
        You are friendly and fun, and you will help the users with their requests.
        Your answers are short and concise."""}
    ]

    while True:
        try:
            # Receive the audio data from the client
            start_time = time.perf_counter()  # Start the timer
            audio_data = await websocket.recv()
            logging.info("Audio data received from client.")

            # Process audio data in-memory using BytesIO
            audio_file = 'received_audio.wav'
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
            logging.info("Audio data saved as 'received_audio.wav'")

            # Process the audio and generate response asynchronously
            user_input, response_text = await process_audio(audio_file, chat_history)

            if not response_text:
                await websocket.send("I didn't catch that. Could you repeat?")
                continue

            if response_text == "Goodbye!":
                await websocket.send("Goodbye!")
                await websocket.close()
                break

            # Start timing for text-to-speech
            tts_start_time = time.perf_counter()

            # Convert response to speech asynchronously
            output_file = 'output.mp3' if tts_model in ['openai', 'elevenlabs', 'melotts', 'cartesia'] else 'output.wav'
            tts_api_key = get_tts_api_key()

            # Run text to speech conversion asynchronously
            await asyncio.to_thread(text_to_speech, tts_model, tts_api_key, response_text, output_file, Config.LOCAL_MODEL_PATH)

            tts_end_time = time.perf_counter()
            tts_time = tts_end_time - tts_start_time
            logging.info(f"TTS conversion took {tts_time:.3f} seconds")

            # Send the audio file back to the client
            with open(output_file, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                await websocket.send(audio_bytes)

            # Clean up
            delete_file(output_file)

            # Measure total response time
            end_time = time.perf_counter()
            total_response_time = end_time - start_time
            logging.info(f"Total response time: {total_response_time:.3f} seconds")

        except websockets.ConnectionClosed:
            logging.info("Client disconnected.")
            break
        except Exception as e:
            logging.error(f"Error: {e}")
            await websocket.send(f"Error occurred: {str(e)}")


async def start_server():
    async with websockets.serve(handle_client, "localhost", 8765):
        logging.info("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(start_server())
