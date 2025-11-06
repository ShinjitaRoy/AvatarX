import time
import logging
import pyaudio
from src.audio.audio_manager import AudioManager

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("\nAvailable Audio Devices:")
    print("-" * 50)
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"Device {i}: {dev['name']}")
        if 'CABLE' in dev['name']:
            print("  --> VB-Cable device found!")
    p.terminate()

def test_audio():
    # Show all devices first
    list_audio_devices()
    
    am = AudioManager("test")
    print(f"\nSelected device index: {am.input_device_index}")
    
    print("\nRecording 10 seconds - play some audio...")
    am.start_recording()
    
    for i in range(10):
        print(f"Recording... {i+1}/10s (frames: {len(am.frames)})")
        time.sleep(1)
    
    print("Stopping...")
    am.stop_recording()

if __name__ == "__main__":
    test_audio()