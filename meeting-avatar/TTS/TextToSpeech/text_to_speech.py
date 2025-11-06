import os
import logging
import threading
import shutil
from datetime import datetime
from gtts import gTTS

# GUI imports (optional, keep GUI functionality working)
import tkinter as tk
from tkinter import ttk, messagebox

# Optional playback dependency
try:
    import pygame
except Exception:
    pygame = None

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TextToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Text to Speech Converter")
        self.root.geometry("600x400")

        # Initialize pygame mixer if available
        if pygame:
            try:
                pygame.mixer.init()
            except Exception as e:
                log.debug("pygame mixer init failed: %s", e)

        # Create output directory if it doesn't exist
        if not os.path.exists("output"):
            os.makedirs("output")

        # Create the main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Text input
        self.text_label = ttk.Label(self.main_frame, text="Enter text:")
        self.text_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.text_input = tk.Text(self.main_frame, height=10, width=50)
        self.text_input.grid(row=1, column=0, columnspan=2, pady=5)

        # Buttons
        self.convert_button = ttk.Button(self.main_frame, text="Convert to Speech", command=self.convert_to_speech)
        self.convert_button.grid(row=2, column=0, pady=10, padx=5)

        self.save_button = ttk.Button(self.main_frame, text="Save Audio", command=self.save_audio)
        self.save_button.grid(row=2, column=1, pady=10, padx=5)

        # Status label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        # Instance variables
        self.current_audio = None

    def convert_to_speech(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text!")
            return

        def convert():
            try:
                self.status_label.config(text="Converting...")
                self.convert_button.state(['disabled'])
                self.save_button.state(['disabled'])

                # Create temporary file in output dir
                out_dir = "output"
                os.makedirs(out_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_file = os.path.join(out_dir, f"temp_speech_{timestamp}.mp3")

                tts = gTTS(text=text, lang='en')
                tts.save(temp_file)
                self.current_audio = temp_file

                # Play with pygame if available
                if pygame:
                    try:
                        pygame.mixer.music.load(temp_file)
                        pygame.mixer.music.play()
                    except Exception as e:
                        log.debug("pygame playback failed: %s", e)

                self.status_label.config(text="Conversion complete")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
                self.status_label.config(text="")
            finally:
                try:
                    self.convert_button.state(['!disabled'])
                    self.save_button.state(['!disabled'])
                except Exception:
                    pass

        # Run conversion in a separate thread
        threading.Thread(target=convert, daemon=True).start()

    def save_audio(self):
        if not self.current_audio:
            messagebox.showwarning("Warning", "Please convert text to speech first!")
            return

        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not os.path.exists("output"):
                os.makedirs("output", exist_ok=True)
            filename = f"output/speech_{timestamp}.mp3"

            # Copy the temporary file to output directory
            with open(self.current_audio, 'rb') as source:
                with open(filename, 'wb') as target:
                    target.write(source.read())

            messagebox.showinfo("Success", f"Audio saved as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save audio: {str(e)}")

# Add this helper so other modules can call it
def convert_text_to_audio(text: str, output_dir: str = "TTS/TextToSpeech/output") -> str:
    """
    Convert 'text' to an mp3 using gTTS and return the filepath.
    Creates output_dir if missing and logs errors.
    This is the helper used by src.audio.audio_manager.AudioManager._save_summary.
    """
    logger = logging.getLogger(__name__)
    logger.debug("convert_text_to_audio: creating audio in %s", output_dir)
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"speech_{timestamp}.mp3"
    out_path = os.path.join(output_dir, filename)
    try:
        tts = gTTS(text=text, lang='en')
        tts.save(out_path)
        logger.info("convert_text_to_audio: saved %s", out_path)
        return out_path
    except Exception as e:
        logger.error("convert_text_to_audio failed: %s", e)
        raise

if __name__ == "__main__":
    # Simple standalone GUI runner
    try:
        root = tk.Tk()
        app = TextToSpeechApp(root)
        root.mainloop()
    except Exception as e:
        log.error("TTS GUI failed: %s", e)