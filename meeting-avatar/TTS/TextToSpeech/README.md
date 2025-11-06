# Text-to-Speech Application

A simple Python application that converts text to speech using Google's Text-to-Speech (gTTS) API with a graphical user interface.

## Features

- Convert text to speech using Google's TTS engine
- Simple and intuitive graphical user interface
- Save audio output as MP3 files
- Support for multiple languages (default: English)

## Requirements

- Python 3.x
- gTTS library
- tkinter (usually comes with Python)
- pygame (for audio playback)

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python text_to_speech.py
   ```
2. Enter your text in the text box
3. Click "Convert to Speech" to hear the audio
4. Click "Save Audio" to save the speech as an MP3 file

## Note

- Internet connection is required as the application uses Google's Text-to-Speech service
- The saved audio files will be stored in the 'output' directory