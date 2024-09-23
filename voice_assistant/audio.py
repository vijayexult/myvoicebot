# import pyaudio
# import wave
# import threading
# import time

# class AudioRecorder:
#     def __init__(self):
#         self.FORMAT = pyaudio.paInt16
#         self.CHANNELS = 1
#         self.RATE = 44100
#         self.CHUNK = 1024
#         self.audio = pyaudio.PyAudio()
#         self.stream = None
#         self.frames = []
#         self.recording = False

#     def start_recording(self):
#         self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
#                                     rate=self.RATE, input=True,
#                                     frames_per_buffer=self.CHUNK)
#         self.recording = True
#         threading.Thread(target=self.record_audio).start()

#     def stop_recording(self):
#         self.recording = False
#         self.stream.stop_stream()
#         self.stream.close()
#         self.audio.terminate()

#     def record_audio(self):
#         while self.recording:
#             data = self.stream.read(self.CHUNK)
#             self.frames.append(data)

#     def save_recording(self, output_file):
#         wave_file = wave.open(output_file, 'wb')
#         wave_file.setnchannels(self.CHANNELS)
#         wave_file.setsampwidth(self.audio.get_sample_size(self.FORMAT))
#         wave_file.setframerate(self.RATE)
#         wave_file.writeframes(b''.join(self.frames))
#         wave_file.close()

# def record_audio(output_file):
#     recorder = AudioRecorder()
#     recorder.start_recording()
#     time.sleep(5)  # Record for 5 seconds
#     recorder.stop_recording()
#     recorder.save_recording(output_file)

# def play_audio(input_file):
#     audio = pyaudio.PyAudio()
#     wave_file = wave.open(input_file, 'rb')
#     stream = audio.open(format=audio.get_format_from_width(wave_file.getsampwidth()),
#                         channels=wave_file.getnchannels(),
#                         rate=wave_file.getframerate(),
#                         output=True)
#     data = wave_file.readframes(1024)
#     while data:
#         stream.write(data)
#         data = wave_file.readframes(1024)
#     stream.stop_stream()
#     stream.close()
#     audio.terminate()


# voice_assistant/audio.py

import speech_recognition as sr
import pygame
import time
import logging
import pydub
from io import BytesIO
from pydub import AudioSegment
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@lru_cache(maxsize=None)
def get_recognizer():
    """
    Return a cached speech recognizer instance
    """
    return sr.Recognizer()

def record_audio(file_path, timeout=10, phrase_time_limit=None, retries=3, energy_threshold=2000, 
                 pause_threshold=1, phrase_threshold=0.1, dynamic_energy_threshold=True, 
                 calibration_duration=1):
    """
    Record audio from the microphone and save it as an MP3 file.
    
    Args:
    file_path (str): The path to save the recorded audio file.
    timeout (int): Maximum time to wait for a phrase to start (in seconds).
    phrase_time_limit (int): Maximum time for the phrase to be recorded (in seconds).
    retries (int): Number of retries if recording fails.
    energy_threshold (int): Energy threshold for considering whether a given chunk of audio is speech or not.
    pause_threshold (float): How much silence the recognizer interprets as the end of a phrase (in seconds).
    phrase_threshold (float): Minimum length of a phrase to consider for recording (in seconds).
    dynamic_energy_threshold (bool): Whether to enable dynamic energy threshold adjustment.
    calibration_duration (float): Duration of the ambient noise calibration (in seconds).
    """
    recognizer = get_recognizer()
    recognizer.energy_threshold = energy_threshold
    recognizer.pause_threshold = pause_threshold
    recognizer.phrase_threshold = phrase_threshold
    recognizer.dynamic_energy_threshold = dynamic_energy_threshold
    
    for attempt in range(retries):
        try:
            with sr.Microphone() as source:
                logging.info("Calibrating for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=calibration_duration)
                logging.info("Recording started")
                # Listen for the first phrase and extract it into audio data
                audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                logging.info("Recording complete")

                # Convert the recorded audio data to an MP3 file
                wav_data = audio_data.get_wav_data()
                audio_segment = pydub.AudioSegment.from_wav(BytesIO(wav_data))
                mp3_data = audio_segment.export(file_path, format="mp3", bitrate="128k", parameters=["-ar", "22050", "-ac", "1"])
                return
        except sr.WaitTimeoutError:
            logging.warning(f"Listening timed out, retrying... ({attempt + 1}/{retries})")
        except Exception as e:
            logging.error(f"Failed to record audio: {e}")
            if attempt == retries -1:
                raise
        
    logging.error("Recording failed after all retries")

def play_audio(file_path):
    """
    Play an audio file using pygame.
    
    Args:
    file_path (str): The path to the audio file to play.
    """
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
    except pygame.error as e:
        logging.error(f"Failed to play audio: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while playing audio: {e}")
    finally:
        pygame.mixer.quit()

