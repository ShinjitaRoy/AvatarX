import os
import time
import threading
import wave
import logging
from queue import Queue, Empty

try:
    import pyaudio
except Exception:
    pyaudio = None

# STT/TTS helpers from repo (best-effort imports)
try:
    from STT.SpeechToText.avatar.speech_handler import SpeechHandler
except Exception:
    SpeechHandler = None

try:
    from STT.SpeechToText.ava import process_audio_to_text, summarize_with_gemini
except Exception:
    def process_audio_to_text(path):  # fallback stub
        return ""
    def summarize_with_gemini(text):  # fallback stub
        return ""

try:
    from TTS.TextToSpeech.text_to_speech import convert_text_to_audio
except Exception:
    convert_text_to_audio = None

log = logging.getLogger(__name__)

class AudioManager:
    """
    Minimal AudioManager: records audio, chunk-processes, and guarantees a summary file on stop.
    Use start_meeting_recording(auto_stop_seconds=60) to auto-stop after 60s.
    """

    def __init__(self, meeting_id: str = None):
        self.meeting_id = meeting_id or "unknown"
        self.recording = False
        self.is_meeting_active = False
        self.audio_queue = Queue()
        self.frames = []
        self.transcribed_text = []
        self.chunk = 1024
        self.channels = 1
        self.rate = 16000
        self.format = pyaudio.paInt16 if pyaudio else None

        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.temp_dir = os.path.join(root, "temp")
        self.summaries_dir = os.path.join(root, "summaries")
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.summaries_dir, exist_ok=True)

        self._p = None
        self._stream = None
        self.input_device_index = None
        self.record_thread = None
        self.process_thread = None
        self._auto_stop_timer = None

        # attempt to autodetect an input device index
        if pyaudio:
            try:
                p = pyaudio.PyAudio()
                for i in range(p.get_device_count()):
                    d = p.get_device_info_by_index(i)
                    name = (d.get("name") or "").lower()
                    if d.get("maxInputChannels", 0) > 0:
                        # prefer VB-Cable / CABLE / microphone words
                        if any(k in name for k in ("cable", "vb-audio", "mic", "microphone", "default")):
                            self.input_device_index = i
                            break
                if self.input_device_index is None:
                    try:
                        default = p.get_default_input_device_info()
                        self.input_device_index = default.get("index")
                    except Exception:
                        self.input_device_index = None
                p.terminate()
                log.info("Selected microphone device index=%s", self.input_device_index)
            except Exception as e:
                log.debug("Audio device detection failed: %s", e)

        # optional full-file STT handler
        try:
            self.speech_handler = SpeechHandler() if SpeechHandler else None
        except Exception:
            self.speech_handler = None

    def _save_wave(self, filename: str, audio_data: bytes):
        try:
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self.channels)
                sampwidth = pyaudio.get_sample_size(self.format) if pyaudio else 2
                wf.setsampwidth(sampwidth)
                wf.setframerate(self.rate)
                wf.writeframes(audio_data)
            log.debug("WAV written: %s", filename)
        except Exception as e:
            log.error("Failed to write wave %s: %s", filename, e)
            raise

    def _process_audio(self):
        """Accumulate ~10s chunks and transcribe each chunk (best-effort)."""
        buffer = []
        buffer_duration = 10
        samples_per_chunk = int(self.rate * buffer_duration)
        bytes_per_sample = 2
        target_bytes = samples_per_chunk * self.channels * bytes_per_sample

        while self.is_meeting_active or not self.audio_queue.empty():
            try:
                data = self.audio_queue.get(timeout=1)
                buffer.append(data)
                if sum(len(b) for b in buffer) >= target_bytes:
                    tmp = os.path.join(self.temp_dir, f"chunk_{int(time.time())}.wav")
                    try:
                        self._save_wave(tmp, b"".join(buffer))
                        try:
                            text = process_audio_to_text(tmp) or ""
                        except Exception as e:
                            log.error("Chunk transcription failed: %s", e)
                            text = ""
                        if text.strip():
                            log.info("Transcribed chunk: %s", text[:200])
                            self.transcribed_text.append(text.strip())
                    finally:
                        try:
                            os.remove(tmp)
                        except Exception:
                            pass
                        buffer = []
            except Empty:
                continue
            except Exception as e:
                log.error("Error in audio processing loop: %s", e)
                time.sleep(0.5)
                continue

    def _record_audio(self):
        if not pyaudio:
            log.error("pyaudio not available, cannot record")
            return
        try:
            self._p = pyaudio.PyAudio()
            kwargs = dict(format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk)
            if self.input_device_index is not None:
                kwargs["input_device_index"] = self.input_device_index
            try:
                self._stream = self._p.open(**kwargs)
                log.info("Started recording from device index %s", self.input_device_index)
            except Exception as e:
                log.error("Failed to open audio stream: %s", e)
                return

            while self.recording:
                try:
                    data = self._stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                    try:
                        self.audio_queue.put_nowait(data)
                    except Exception:
                        pass
                except Exception as e:
                    log.error("Error reading audio stream: %s", e)
                    break
        except Exception as e:
            log.error("Unexpected error in _record_audio: %s", e)
        finally:
            try:
                if self._stream:
                    try:
                        self._stream.stop_stream()
                        self._stream.close()
                    except Exception:
                        pass
                    self._stream = None
            except Exception:
                pass
            try:
                if self._p:
                    self._p.terminate()
                    self._p = None
            except Exception:
                pass
            log.info("Stopped recording. Total frames: %d", len(self.frames))

    def _auto_stop_callback(self):
        log.info("Auto-stop timer expired, stopping meeting recording...")
        try:
            self.stop_meeting_recording()
        except Exception as e:
            log.error("Error in auto-stop callback: %s", e)

    def _ensure_stream_open(self):
        """Open PyAudio and input stream synchronously so recording begins immediately."""
        if not pyaudio:
            log.debug("pyaudio not available; cannot open stream")
            return
        try:
            if getattr(self, "_p", None) is None:
                self._p = pyaudio.PyAudio()
            if getattr(self, "_stream", None) is None:
                kwargs = dict(format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk)
                if self.input_device_index is not None:
                    kwargs["input_device_index"] = self.input_device_index
                # open stream now (blocking until ready)
                self._stream = self._p.open(**kwargs)
                log.info("Audio stream opened synchronously (ready to record)")
        except Exception as e:
            log.error("Failed to open audio stream synchronously: %s", e)
            # leave _stream as None; _record_audio will try to recover/open later

    def start_meeting_recording(self, auto_stop_seconds: int = 60):
        """Start recording and processing threads. Auto-stop after auto_stop_seconds (default 60)."""
        self.is_meeting_active = True
        self.recording = True
        self.frames = []
        self.transcribed_text = []

        # Ensure the audio stream is open immediately so the timer start == actual recording start
        try:
            self._ensure_stream_open()
        except Exception as e:
            log.debug("Synchronous stream open failed (will try in thread): %s", e)

        self.record_thread = threading.Thread(target=self._record_audio, daemon=True)
        self.process_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.record_thread.start()
        self.process_thread.start()

        # start auto-stop timer
        try:
            if getattr(self, "_auto_stop_timer", None):
                try:
                    self._auto_stop_timer.cancel()
                except Exception:
                    pass
                self._auto_stop_timer = None
            if auto_stop_seconds and auto_stop_seconds > 0:
                self._auto_stop_timer = threading.Timer(auto_stop_seconds, self._auto_stop_callback)
                self._auto_stop_timer.daemon = True
                self._auto_stop_timer.start()
                log.info("Auto-stop timer set for %ds", auto_stop_seconds)
        except Exception as e:
            log.debug("Failed to start auto-stop timer: %s", e)

        log.info("Started continuous meeting recording")

    start_recording = start_meeting_recording

    def stop_meeting_recording(self):
        """Stop recording and generate summary."""
        if not self.recording:
            return

        log.info("Stopping meeting recording...")
        self.recording = False
        self.is_meeting_active = False

        # Close audio resources
        try:
            if getattr(self, "_stream", None):
                try:
                    self._stream.stop_stream()
                except Exception:
                    pass
                try:
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None
        except Exception as e:
            log.error("Error closing audio stream: %s", e)

        # terminate PyAudio
        try:
            if getattr(self, "_p", None):
                try:
                    self._p.terminate()
                except Exception:
                    pass
                self._p = None
        except Exception as e:
            log.error("Error terminating PyAudio: %s", e)

        # join threads
        try:
            if getattr(self, "record_thread", None):
                self.record_thread.join(timeout=5)
        except Exception as e:
            log.debug("record_thread join error: %s", e)
        try:
            if getattr(self, "process_thread", None):
                self.process_thread.join(timeout=15)
        except Exception as e:
            log.debug("process_thread join error: %s", e)

        # save final wav (best-effort)
        final_wav = None
        try:
            if self.frames:
                final_wav = os.path.join(self.temp_dir, f"meeting_{self.meeting_id}_{int(time.time())}.wav")
                try:
                    self._save_wave(final_wav, b"".join(self.frames))
                    log.info("Saved final recording: %s (frames=%d)", final_wav, len(self.frames))
                except Exception as e:
                    log.error("Failed to save final wav: %s", e)
                    final_wav = None
        except Exception as e:
            log.error("Error writing final wav: %s", e)
            final_wav = None

        # Get final transcript
        final_text = " ".join(self.transcribed_text).strip()
        log.info(f"Final transcript: {final_text[:200]}...")

        # Generate summary (try Gemini, fallback to transcript)
        summary = ""
        try:
            if final_text:
                try:
                    summary = summarize_with_gemini(final_text) or ""
                    log.info("summarize_with_gemini returned length=%d", len(summary or ""))
                except Exception as e:
                    log.error("summarize_with_gemini failed: %s", e)
                    summary = ""
        except Exception as e:
            log.error("Unexpected error during summarization: %s", e)
            summary = ""

        # If no summary produced, use final transcript as fallback
        if not summary:
            if final_text:
                summary = final_text
                log.info("No summary generated; using transcript as fallback (len=%d)", len(summary))
            else:
                summary = "No transcribed text captured during meeting."
                log.info("No transcript available; using placeholder fallback")

        # Always save and attempt TTS (guaranteed)
        try:
            saved_txt = self._save_summary(summary)
            log.info("Saved meeting summary (or fallback) to: %s", saved_txt)
        except Exception as e:
            log.error("Failed to save summary/fallback: %s", e)

    stop_recording = stop_meeting_recording

    def _save_summary(self, summary: str) -> str:
        """Save meeting summary text and attempt TTS. Return saved text path."""
        if not getattr(self, "meeting_id", None):
            self.meeting_id = "unknown"
        os.makedirs(self.summaries_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        txt_path = os.path.join(self.summaries_dir, f"meeting_{self.meeting_id}_{timestamp}.txt")
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Meeting Summary ({self.meeting_id})\n")
                f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n\n")
                f.write("Summary:\n")
                f.write(summary)
            log.info("Saved summary text to %s", txt_path)
        except Exception as e:
            log.error("Failed to save summary text to %s: %s", txt_path, e)
            raise

        # Write plain last_summary.txt for TTS input
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            tts_text_path = os.path.join(root, "TTS", "TextToSpeech", "last_summary.txt")
            os.makedirs(os.path.dirname(tts_text_path), exist_ok=True)
            with open(tts_text_path, "w", encoding="utf-8") as tf:
                tf.write(summary)
            log.info("Saved last_summary.txt for TTS at %s", tts_text_path)
        except Exception as e:
            log.debug("Could not write last_summary.txt for TTS: %s", e)

        # Best-effort: generate TTS audio from the summary (or fallback transcript)
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            audio_out_dir = os.path.join(root, "TTS", "TextToSpeech", "output")
            os.makedirs(audio_out_dir, exist_ok=True)
            if convert_text_to_audio:
                try:
                    audio_path = convert_text_to_audio(summary, output_dir=audio_out_dir)
                    log.info("Generated TTS audio at %s", audio_path)
                except Exception as e:
                    log.error("convert_text_to_audio failed: %s", e)
            else:
                log.debug("convert_text_to_audio helper not available")
        except Exception as e:
            log.debug("TTS generation step failed (best-effort): %s", e)

        return txt_path