from src.avatar.avatar_renderer import AvatarRenderer
import time

def main():
    renderer = AvatarRenderer(640, 480)
    print("Window created. Please set up OBS capture now.")
    print("Window name to look for in OBS: 'Meeting Avatar'")
    
    try:
        while True:
            frame = renderer.render_frame()
            renderer.display_frame(frame)
            time.sleep(0.033)  # ~30 FPS
    except KeyboardInterrupt:
        print("Closing window...")
        renderer.cleanup()

if __name__ == "__main__":
    main()