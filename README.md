# Meeting Avatar - AI-Powered Meeting Assistant

An intelligent assistant that records, transcribes, summarizes meetings and generates audio summaries using AI.

## Features

- **Speech Recording & Transcription**
  - Real-time audio recording from microphone
  - Speech-to-text transcription using Whisper
  - Support for continuous recording sessions

- **AI-Powered Summarization**
  - Meeting summary generation using Google's Gemini AI
  - Fallback to transcript when summarization fails
  - Summary storage in text files

- **Text-to-Speech Output**
  - Convert meeting summaries to audio using gTTS
  - Audio file generation in MP3 format
  - Built-in audio playback support

## Setup

1. Clone the repository
```powershell
git clone <repository-url>
cd meeting-avatar
```

2. Create and activate virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies
```powershell
pip install -r requirements.txt
```

4. Configure environment variables
- Create `.env` file in project root with:
```
GOOGLE_API_KEY=your_gemini_api_key
```

## Usage

1. Run the speech-to-summary pipeline test:
```powershell
python -m tests.test_speech_summary
```
This will:
- Record 30 seconds of audio
- Transcribe the speech
- Generate an AI summary
- Save summary text file
- Convert to audio (TTS)

2. Check output files:
- Transcripts/Summaries: `summaries/` folder
- Audio files: `TTS/TextToSpeech/output/` folder

## Project Structure

```
meeting-avatar/
├── src/
│   ├── audio/          # Audio recording & processing
│   └── utils/          # Helper utilities
├── STT/                # Speech-to-text functionality
├── TTS/                # Text-to-speech conversion
├── summaries/          # Generated meeting summaries
├── temp/              # Temporary WAV recordings
└── tests/             # Test suite
```

## Dependencies

- Python 3.11+
- PyAudio (audio recording)
- Whisper (speech recognition)
- Google Generative AI (Gemini)
- gTTS (text-to-speech)
- pygame (audio playback)

## Testing

Run individual test modules:
```powershell
python -m tests.test_audio_recording    # Test audio recording
python -m tests.test_speech_summary     # Test full pipeline
python -m tests.test_gemini_models      # Test AI models
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
