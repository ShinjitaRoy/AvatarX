import logging
import numpy as np
from pyvrm import VRM
import pyglet
from pyglet.gl import *

log = logging.getLogger(__name__)

class VRMRenderer:
    def __init__(self, vrm_path: str, width=640, height=480):
        self.width = width
        self.height = height
        
        # Load VRM model
        self.model = VRM.from_file(vrm_path)
        log.info(f"Loaded VRM model: {self.model.meta.title}")
        
        # Create window for rendering (visible so OBS can capture it)
        self.window = pyglet.window.Window(width, height, visible=True)
        self.window.set_caption("Meeting Avatar")  # OBS will see this title
        # Give the window a moment to be created, then try to make it topmost on Windows
        time.sleep(0.05)
        if sys.platform.startswith("win"):
            try:
                hwnd = ctypes.windll.user32.FindWindowW(None, "Meeting Avatar")
                # HWND found -> set topmost (SWP_NOMOVE|SWP_NOSIZE = 0x0002|0x0001)
                if hwnd:
                    ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
            except Exception:
                pass
        
        # Setup 3D rendering
        self.setup_camera()
        
    def setup_camera(self):
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, self.width, self.height)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, self.width/self.height, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, -1, -3)  # Position camera
        
    def render_frame(self):
        """Render one frame of the avatar"""
        self.window.switch_to()
        
        # Clear frame
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Draw VRM model
        self.model.draw()
        
        # Get frame as numpy array
        buffer = pyglet.image.get_buffer_manager().get_color_buffer()
        image_data = buffer.get_image_data()
        arr = np.frombuffer(image_data.get_data(), dtype=np.uint8)
        arr = arr.reshape(self.height, self.width, 4)  # RGBA
        return arr[:, :, :3]  # Convert to RGB
        
    def update_expression(self, expression_name: str, weight: float = 1.0):
        """Update facial expression/blend shape"""
        if expression_name in self.model.blend_shapes:
            self.model.blend_shapes[expression_name] = weight
            
    def update_bone(self, bone_name: str, rotation):
        """Update bone rotation (e.g., for head movement)"""
        if bone_name in self.model.bones:
            self.model.bones[bone_name].rotation = rotation
            
    def cleanup(self):
        """Clean up resources"""
        self.window.close()