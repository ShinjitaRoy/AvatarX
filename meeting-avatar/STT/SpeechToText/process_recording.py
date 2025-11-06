from avatar import Avatar
import pyaudio
import wave

def record_audio(duration=5, filename="recorded_speech.wav"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    print("* recording")
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    frames = []
    
    for i in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    print("* done recording")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return filename

# Create avatar instance
avatar = Avatar()

# First record some audio
print("Recording audio for 5 seconds...")
audio_path = record_audio(duration=5, filename="recorded_speech.wav")
print(f"Audio saved to: {audio_path}")

# Process the audio file
print("Processing audio file...")
text = avatar.speech_handler.speech_to_text(audio_path, language='en')
summary = avatar.text_processor.summarize_text(text)

print("\n=== Full Transcript ===")
print(text)
print("\n=== Meeting Summary ===")
print(summary)

# Convert summary to speech
print("\nConverting summary to speech...")
avatar.summarize_and_speak(summary)

print("\nDone! The summary has been spoken out loud and saved as an audio file.")

# Clean up when done
avatar.cleanup_temp_files()