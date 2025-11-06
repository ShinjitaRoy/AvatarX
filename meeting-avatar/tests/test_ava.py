from STT.SpeechToText.ava import record_audio, process_audio_to_text, summarize_with_gemini
import os
from dotenv import load_dotenv

def test_speech_pipeline():
    # Load environment variables
    load_dotenv()
    
    print("\n1. Recording 10 seconds of audio...")
    print("Please speak into your microphone...")
    audio_file = record_audio(duration=10, filename="temp/test_recording.wav")
    
    print("\n2. Converting speech to text...")
    text = process_audio_to_text(audio_file)
    if text:
        print(f"\nTranscribed Text:\n{text}")
        
        print("\n3. Generating summary...")
        summary = summarize_with_gemini(text)
        if summary:
            print(f"\nSummary:\n{summary}")
    else:
        print("No transcription generated. Check your microphone.")

if __name__ == "__main__":
    test_speech_pipeline()