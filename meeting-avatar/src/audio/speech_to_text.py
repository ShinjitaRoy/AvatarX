import speech_recognition as sr
import logging

class SpeechToText:
    def __init__(self, language="en-US"):
        self.recognizer = sr.Recognizer()
        self.language = language

    def transcribe_audio(self, audio):
        try:
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text
        except sr.UnknownValueError:
            logging.warning("Speech not understood")
            return ""
        except Exception as e:
            logging.error(f"STT error: {e}")
            return ""