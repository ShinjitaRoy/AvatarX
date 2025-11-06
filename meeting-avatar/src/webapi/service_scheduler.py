import threading
import logging
from src.meeting.meeting_controller import MeetingController
import time

log = logging.getLogger(__name__)

class ServiceScheduler:
    """
    Singleton-style scheduler wrapper around MeetingController.
    Keeps a simple in-memory list of scheduled meetings (for API list).
    Starts a background thread running the MeetingController.run_loop.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceScheduler, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.meeting_controller = MeetingController()
        self._scheduled = []
        self._loop_thread = threading.Thread(target=self._run_scheduler_loop, daemon=True)
        self._loop_thread.start()
        log.info("ServiceScheduler background loop started")

    def _run_scheduler_loop(self):
        """Run scheduler in a separate thread with error handling"""
        while True:
            try:
                self.meeting_controller.run_loop()
            except Exception as e:
                log.error(f"Scheduler loop error (will retry): {e}")
                time.sleep(5)

    def schedule_meeting(self, meeting_id: str, password: str, start_time_str: str):
        self.meeting_controller.schedule_meeting(meeting_id, password, start_time_str)
        item = {"meeting_id": meeting_id, "password": password, "start_time": start_time_str}
        self._scheduled.append(item)
        log.info("Scheduled meeting %s at %s", meeting_id, start_time_str)
        return item

    def list_scheduled(self):
        return list(self._scheduled)

    def start_now(self, meeting_id: str, password: str):
        return self.meeting_controller._start_meeting(meeting_id, password)

    def leave(self):
        return self.meeting_controller.leave_meeting()