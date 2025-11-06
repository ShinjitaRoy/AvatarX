import unittest
from src.audio.audio_capture import AudioCapture
from src.audio.speech_to_text import SpeechToText

class TestAudioCapture(unittest.TestCase):
    def setUp(self):
        self.audio_capture = AudioCapture()

    def test_audio_capture_initialization(self):
        self.assertIsNotNone(self.audio_capture)

    def test_start_capture(self):
        result = self.audio_capture.start_capture()
        self.assertTrue(result)

    def test_stop_capture(self):
        self.audio_capture.start_capture()
        result = self.audio_capture.stop_capture()
        self.assertTrue(result)

class TestSpeechToText(unittest.TestCase):
    def setUp(self):
        self.speech_to_text = SpeechToText()

    def test_speech_to_text_initialization(self):
        self.assertIsNotNone(self.speech_to_text)

    def test_convert_audio_to_text(self):
        audio_data = "sample_audio_data"  # Replace with actual audio data for testing
        result = self.speech_to_text.convert(audio_data)
        self.assertIsInstance(result, str)

if __name__ == '__main__':
    unittest.main()