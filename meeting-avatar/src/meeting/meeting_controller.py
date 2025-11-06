import schedule
import time
import logging
import threading
from .zoom_client import ZoomClient
from src.audio.audio_manager import AudioManager

log = logging.getLogger(__name__)

class MeetingController:
    def __init__(self):
        self.zoom = ZoomClient()
        self.scheduled_jobs = []
        self.audio_manager = None

    def schedule_meeting(self, meeting_id, password, start_time_str):
        try:
            log.info(f"Scheduling meeting {meeting_id} for {start_time_str}")
            job = schedule.every().day.at(start_time_str).do(self._start_meeting, meeting_id, password)
            self.scheduled_jobs.append(job)
            log.info(f"Successfully scheduled job for {start_time_str}")
            # Print next run time
            log.info(f"Next run time: {job.next_run}")
            return True
        except Exception as e:
            log.error(f"Failed to schedule meeting: {e}")
            return False

    def _start_meeting(self, meeting_id, password):
        try:
            success = self.zoom.join(meeting_id, password)
            if success:
                # start recording
                self.audio_manager = AudioManager(meeting_id)
                self.audio_manager.start_meeting_recording()
                log.info(f"Started continuous recording for meeting {meeting_id}")

                # watcher thread: waits until Zoom client signals meeting end and then cleans up
                def _watch_meeting_and_cleanup():
                    try:
                        log.info("Watcher: waiting for meeting to end...")
                        left = self.zoom.wait_until_left()   # should block until meeting ended
                        log.info(f"Watcher: wait_until_left returned: {left}")
                        if left:
                            log.info("Watcher: meeting ended -> performing cleanup")
                            try:
                                self.leave_meeting()
                            except Exception as e:
                                log.error(f"Watcher: error during leave_meeting: {e}")
                    except Exception as e:
                        log.error(f"Watcher: unexpected error: {e}")

                watcher = threading.Thread(target=_watch_meeting_and_cleanup, daemon=True)
                watcher.start()

            return success
        except Exception as e:
            log.error(f"Failed to start meeting: {e}")
            return False

    def leave_meeting(self):
        try:
            # stop recording first (if active)
            if getattr(self, "audio_manager", None):
                log.info("Controller: stopping meeting recording via leave_meeting")
                try:
                    self.audio_manager.stop_meeting_recording()
                except Exception as e:
                    log.error(f"Error stopping audio manager: {e}")
                self.audio_manager = None

            # then leave Zoom
            if getattr(self, "zoom", None):
                self.zoom.leave()
            return True
        except Exception as e:
            log.error(f"Error leaving meeting: {e}")
            return False

    def run_loop(self):
        log.info("Starting scheduler loop")
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                log.error(f"Error in scheduler loop: {e}")