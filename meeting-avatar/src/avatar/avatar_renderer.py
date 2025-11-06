import cv2
import numpy as np
import logging
import time

class AvatarRenderer:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.window_name = "Meeting Avatar"  # Specific window name
        
        # Create window with specific parameters
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_EXPANDED)
        cv2.resizeWindow(self.window_name, width, height)
        # Move window to visible position
        cv2.moveWindow(self.window_name, 100, 100)

    def render_frame(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Draw avatar (simple circle face)
        center = (self.width // 2, self.height // 2)
        cv2.circle(frame, center, 100, (50, 200, 50), -1)  # Green face
        
        # Add text to confirm window name
        cv2.putText(frame, 
                   self.window_name,
                   (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   1, 
                   (255, 255, 255), 
                   2)
        
        return frame

    def display_frame(self, frame):
        cv2.imshow(self.window_name, frame)
        # Longer wait time to keep window responsive
        cv2.waitKey(1)

    def cleanup(self):
        cv2.destroyAllWindows()