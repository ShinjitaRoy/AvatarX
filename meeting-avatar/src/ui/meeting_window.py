import tkinter as tk
from tkinter import ttk, messagebox
from src.meeting.meeting_controller import MeetingController
import logging

class MeetingWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Meeting Avatar")
        self.root.geometry("400x300")
        self.root.configure(bg='#f0f0f0')
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Meeting ID input
        ttk.Label(self.main_frame, text="Meeting ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.meeting_id = ttk.Entry(self.main_frame, width=30)
        self.meeting_id.grid(row=0, column=1, pady=5)
        
        # Password input
        ttk.Label(self.main_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password = ttk.Entry(self.main_frame, width=30, show="*")
        self.password.grid(row=1, column=1, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Buttons frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Join button
        self.join_btn = ttk.Button(button_frame, text="Join Meeting", command=self.join_meeting)
        self.join_btn.pack(side=tk.LEFT, padx=5)
        
        # Leave button (disabled initially)
        self.leave_btn = ttk.Button(button_frame, text="Leave Meeting", command=self.leave_meeting, state=tk.DISABLED)
        self.leave_btn.pack(side=tk.LEFT, padx=5)
        
        self.meeting_controller = None
        
    def join_meeting(self):
        meeting_id = self.meeting_id.get().strip()
        password = self.password.get().strip()
        
        if not meeting_id:
            messagebox.showerror("Error", "Please enter a meeting ID")
            return
            
        try:
            self.status_var.set("Connecting...")
            self.join_btn.configure(state=tk.DISABLED)
            
            # Initialize controller if needed
            if not self.meeting_controller:
                self.meeting_controller = MeetingController()
            
            # Join the meeting
            success = self.meeting_controller._start_meeting(meeting_id, password)
            
            if success:
                self.status_var.set("Connected to meeting")
                self.leave_btn.configure(state=tk.NORMAL)
            else:
                self.status_var.set("Failed to join meeting")
                self.join_btn.configure(state=tk.NORMAL)
                
        except Exception as e:
            logging.error(f"Failed to join meeting: {e}")
            self.status_var.set("Error joining meeting")
            self.join_btn.configure(state=tk.NORMAL)
            messagebox.showerror("Error", f"Failed to join meeting: {str(e)}")
            
    def leave_meeting(self):
        try:
            if self.meeting_controller:
                self.meeting_controller.leave_meeting()
            self.status_var.set("Left meeting")
            self.join_btn.configure(state=tk.NORMAL)
            self.leave_btn.configure(state=tk.DISABLED)
        except Exception as e:
            logging.error(f"Error leaving meeting: {e}")
            messagebox.showerror("Error", f"Error leaving meeting: {str(e)}")
            
    def run(self):
        self.root.mainloop()