# meeting-avatar/meeting-avatar/README.md

# Meeting Avatar

This project is designed to create an avatar that can automatically join Zoom meetings on behalf of a user. The avatar captures audio, performs speech-to-text conversion, and summarizes the meeting for the user. If the user joins the meeting midway, the avatar will exit the meeting.

## Features

- Automatic joining of Zoom meetings
- Audio capture from meetings
- Speech-to-text conversion
- Meeting summary generation
- Avatar animation during meetings

## Project Structure

```
meeting-avatar
├── src
│   ├── main.py
│   ├── config
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── avatar
│   │   ├── __init__.py
│   │   ├── avatar_controller.py
│   │   └── animation_handler.py
│   ├── meeting
│   │   ├── __init__.py
│   │   ├── meeting_controller.py
│   │   ├── zoom_client.py
│   │   └── meeting_scheduler.py
│   ├── audio
│   │   ├── __init__.py
│   │   ├── audio_capture.py
│   │   └── speech_to_text.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── summarizer.py
│   │   └── logger.py
│   └── database
│       ├── __init__.py
│       └── db_handler.py
├── tests
│   ├── __init__.py
│   ├── test_avatar.py
│   ├── test_meeting.py
│   └── test_audio.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```
   cd meeting-avatar
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables in the `.env` file.

## Usage

To run the application, execute the following command:
```
python src/main.py
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License.