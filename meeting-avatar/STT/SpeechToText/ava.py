import os
import wave
import pyaudio
import whisper
import google.generativeai as genai
import numpy as np
from datetime import datetime
from STT.SpeechToText.avatar import Avatar  # Use full package path
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Load Whisper model
model = whisper.load_model("base")

# ensure temp directory exists
if not os.path.exists('temp'):
    os.makedirs('temp')

# Load Gemini API key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

def record_audio(duration=30, filename="temp/recording.wav"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    frames = []
    stream = None
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
    finally:
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    return filename

def split_on_silence(wav_path, min_segment_s=0.5, frame_ms=30, hop_ms=15, silence_thresh_factor=0.5, max_silence_s=0.5):
    wf = wave.open(wav_path, 'rb')
    sr = wf.getframerate()
    n_channels = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    raw = wf.readframes(wf.getnframes())
    wf.close()

    dtype = np.int16 if sampwidth == 2 else np.int8
    audio = np.frombuffer(raw, dtype=dtype)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1).astype(dtype)

    audio_f = audio.astype(np.float32) / np.iinfo(dtype).max

    frame_len = int(sr * frame_ms / 1000)
    hop = int(sr * hop_ms / 1000)
    if frame_len <= 0: frame_len = 1024
    if hop <= 0: hop = frame_len // 2

    # compute short-time energy
    frames = []
    for start in range(0, len(audio_f) - frame_len + 1, hop):
        f = audio_f[start:start + frame_len]
        frames.append(np.mean(f * f))
    energy = np.array(frames)

    # dynamic threshold
    thresh = max(energy.mean() * silence_thresh_factor, 1e-8)

    voiced = energy > thresh

    # merge voiced frames into segments, allow short silences inside segments
    max_silence_frames = int(max_silence_s / (hop / sr))
    segments = []
    i = 0
    while i < len(voiced):
        if not voiced[i]:
            i += 1
            continue
        # start of segment
        start_frame = i
        j = i
        silence_count = 0
        while j < len(voiced):
            if voiced[j]:
                silence_count = 0
            else:
                silence_count += 1
            if silence_count > max_silence_frames:
                break
            j += 1
        end_frame = j
        seg_start_sample = max(0, start_frame * hop)
        seg_end_sample = min(len(audio_f), (end_frame * hop) + frame_len)
        seg_duration = (seg_end_sample - seg_start_sample) / sr
        if seg_duration >= min_segment_s:
            segments.append((seg_start_sample, seg_end_sample))
        i = end_frame + 1

    # write segments to files
    seg_files = []
    for idx, (s, e) in enumerate(segments, start=1):
        seg_audio = (audio_f[s:e] * np.iinfo(dtype).max).astype(dtype).tobytes()
        out_path = f"temp/segment_{idx}.wav"
        wfw = wave.open(out_path, 'wb')
        wfw.setnchannels(1)
        wfw.setsampwidth(sampwidth)
        wfw.setframerate(sr)
        wfw.writeframes(seg_audio)
        wfw.close()
        seg_files.append(out_path)

    return seg_files

def process_audio_to_text(audio_path):
    """
    Transcribe audio file using Whisper
    """
    try:
        # Transcribe with Whisper
        result = model.transcribe(audio_path)
        transcribed_text = result["text"].strip()
        
        if transcribed_text:
            print(f"Transcribed: {transcribed_text}")
            return transcribed_text
        return None
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

def summarize_with_chatgpt(text, model="gpt-3.5-turbo", max_tokens=300, temperature=0.2):
    """
    Summarize `text` using OpenAI Chat API. Requires OPENAI_API_KEY env var.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Use: $env:OPENAI_API_KEY='sk-...' (PowerShell) or setx OPENAI_API_KEY 'value'")
    openai.api_key = api_key

    prompt = (
        "You are a helpful assistant. Summarize the following transcribed conversation or speech. "
        "Keep the summary concise and include key points only.\n\n"
        f"{text}"
    )

    resp = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful summarizer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()

def summarize_with_gemini(text: str) -> str:
    """Summarize text using Gemini Pro API."""
    try:
        # Load and verify API key
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise ValueError("Please set a valid GOOGLE_API_KEY in .env file")

        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')

        # Skip if no text to summarize
        if not text or not text.strip():
            log.warning("No text provided for summarization")
            return "No transcribed text to summarize"

        # Generate summary
        prompt = f"""
        Summarize this meeting transcript in 2-3 sentences, focusing on key points discussed:

        Transcript:
        {text}
        """
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        log.info(f"Generated summary: {summary[:100]}...")
        return summary

    except ValueError as e:
        log.error(f"API key error: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        log.error(f"Summarization failed: {e}")
        return f"Failed to generate summary: {str(e)}"

class TranscriptionVisualizer:
    def __init__(self):
        self.segments = []
        self.durations = []
        self.word_counts = []
        self.timestamps = []

    def add_segment(self, text, duration):
        self.segments.append(text)
        self.durations.append(duration)
        self.word_counts.append(len(text.split()))
        self.timestamps.append(datetime.now())

    def plot_metrics(self):
        plt.figure(figsize=(12, 6))
        
        # Create subplots
        plt.subplot(1, 2, 1)
        plt.bar(range(len(self.word_counts)), self.word_counts, color='skyblue')
        plt.title('Words per Segment')
        plt.xlabel('Segment Number')
        plt.ylabel('Word Count')

        plt.subplot(1, 2, 2)
        plt.bar(range(len(self.durations)), self.durations, color='lightgreen')
        plt.title('Segment Durations')
        plt.xlabel('Segment Number')
        plt.ylabel('Duration (seconds)')

        plt.tight_layout()
        
        # Save the plot
        if not os.path.exists('visualizations'):
            os.makedirs('visualizations')
        plt.savefig('visualizations/stt_metrics.png')
        plt.close()

# Modify main section
if __name__ == "__main__":
    avatar = Avatar()
    visualizer = TranscriptionVisualizer()

    print("Recording for 5 seconds. Speak one at a time.")
    recording = record_audio(duration=5, filename="temp/recording.wav")
    print("Saved recording to:", recording)

    print("Detecting speech segments...")
    segments = split_on_silence(recording)

    transcripts = []
    if not segments:
        print("No speech detected.")
    else:
        for i, seg_file in enumerate(segments):
            try:
                start_time = datetime.now()
                text = avatar.speech_handler.speech_to_text(seg_file, language='en')
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                if text:
                    transcripts.append(text.strip())
                    print(text.strip())
                    # Add to visualizer
                    visualizer.add_segment(text.strip(), duration)
            except Exception as e:
                print(f"Error in segment {i+1}:", str(e))

    # Create combined transcript
    if transcripts:
        combined = " ".join(transcripts)
        print("\nComplete Transcript:")
        print(combined)

        # Generate visualization
        visualizer.plot_metrics()
        print("\nVisualization saved to 'visualizations/stt_metrics.png'")

        # Try summarizing with Gemini
        try:
            summary = summarize_with_gemini(combined)
            print("\nSummary:")
            print(summary)
        except Exception as e:
            print("\nFailed to summarize:", str(e))

    # Cleanup
    try:
        avatar.cleanup_temp_files()
    except Exception:
        pass