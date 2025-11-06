import speech_recognition as sr
import logging

class AudioCapture:
    def __init__(self, language="en-US"):
        self.recognizer = sr.Recognizer()
        self.language = language

    def listen_once(self, source=None, timeout=5):
        # Use system microphone or audio stream from meeting client
        with sr.Microphone() as mic:
            logging.info("Listening for audio...")
            audio = self.recognizer.listen(mic, timeout=timeout)
            return audio