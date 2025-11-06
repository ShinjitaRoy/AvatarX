import threading
import logging
from .vrm_renderer import VRMRenderer
from .animation_handler import AnimationHandler

class AvatarController:
    def __init__(self, vrm_path=None):
        self.vrm_path = vrm_path or "models/default_avatar.vrm"
        self.renderer = None
        self.active = False
        self.thread = None
        self.in_meeting = False
        self.anim = AnimationHandler()

    def activate(self):
        if self.active:
            return
        # Initialize VRM renderer
        try:
            self.renderer = VRMRenderer(self.vrm_path)
            self.active = True
            self.thread = threading.Thread(target=self._run_animation, daemon=True)
            self.thread.start()
            logging.info("VRM avatar activated")
        except Exception as e:
            logging.error(f"Failed to initialize VRM renderer: {e}")
            raise

    def _run_animation(self):
        while self.active and self.renderer:
            try:
                # Render frame and update to virtual camera
                frame = self.renderer.render_frame()
                # Update expressions/poses based on animation state
                if self.anim.current == "idle":
                    self.renderer.update_expression("neutral", 1.0)
                elif self.anim.current == "talking":
                    self.renderer.update_expression("aa", 0.5)
                # TODO: Add more animations/expressions
            except Exception as e:
                logging.error(f"Animation error: {e}")
                break

    def deactivate(self):
        self.active = False
        if self.renderer:
            self.renderer.cleanup()
            self.renderer = None
        logging.info("Avatar deactivated")

    # Methods required by tests
    def join_meeting(self, meeting_id: str) -> bool:
        logging.info(f"Avatar joining meeting {meeting_id}")
        self.in_meeting = True
        self.activate()
        # start a default animation to show presence
        self.anim.start_animation("idle")
        return True

    def exit_meeting(self) -> bool:
        logging.info("Avatar exiting meeting")
        self.in_meeting = False
        self.anim.stop_animation()
        self.deactivate()
        return True