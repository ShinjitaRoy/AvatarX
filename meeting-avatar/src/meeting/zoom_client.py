import logging
import json
import time
import os
from playwright.sync_api import sync_playwright, TimeoutError

log = logging.getLogger(__name__)

class ZoomClient:
    def __init__(self, headless: bool = False):
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.in_meeting = False
        self.headless = headless

    def start_playwright(self):
        if self._playwright is None:
            self._playwright = sync_playwright().start()

    def stop_playwright(self):
        try:
            if self.page:
                try:
                    self.page.close()
                except Exception:
                    pass
                self.page = None
            if self.context:
                try:
                    self.context.close()
                except Exception:
                    pass
                self.context = None
            if self.browser:
                try:
                    self.browser.close()
                except Exception:
                    pass
                self.browser = None
            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
        finally:
            self.in_meeting = False

    def _dump_detected_devices(self):
        """
        Evaluate enumerateDevices in page and save list to disk & logs.
        Returns python list of device dicts (kind, label, deviceId).
        """
        js = r"""
        () => {
            try {
                return navigator.mediaDevices.enumerateDevices()
                    .then(devs => devs.map(d => ({ kind: d.kind, label: d.label || '', deviceId: d.deviceId })))
                    .catch(e => ({ error: String(e) }));
            } catch (err) {
                return { error: String(err) };
            }
        }
        """
        try:
            res = self.page.evaluate(js)
            # ensure JSON-serializable
            if isinstance(res, dict) and res.get("error"):
                log.warning("enumerateDevices returned error: %s", res.get("error"))
                return []
            devices = res if isinstance(res, list) else []
            try:
                with open("zoom_detected_devices.json", "w", encoding="utf-8") as f:
                    json.dump(devices, f, indent=2)
                log.info("Saved zoom_detected_devices.json")
            except Exception as e:
                log.debug("Failed to write device dump: %s", e)
            log.info("detected_devices: %s", devices)
            return devices
        except Exception as e:
            log.exception("Failed to evaluate enumerateDevices: %s", e)
            return []

    def _force_camera_selection(self, preferred_names=("obs", "virtual")):
        """
        Try multiple strategies to ensure OBS virtual camera is used.
        Returns result string for logs.
        """
        devices = self._dump_detected_devices()
        obs_dev = None
        for d in devices:
            if d.get("kind") == "videoinput" and any(n.lower() in (d.get("label") or "").lower() for n in preferred_names):
                obs_dev = d
                break

        if obs_dev:
            log.info("Found OBS candidate before selection: %s", obs_dev.get("label"))
        else:
            log.info("No OBS candidate found yet; will prompt permissions to reveal labels")

        camera_js = r"""
        (deviceId) => {
            const sleep = ms => new Promise(r => setTimeout(r, ms));
            return (async () => {
                try {
                    // stop existing streams in page
                    try {
                        document.querySelectorAll('video').forEach(v => {
                            try { if (v.srcObject) { v.srcObject.getTracks().forEach(t => t.stop()); v.srcObject = null; } } catch(e){}
                        });
                    } catch(e){}

                    // If deviceId known, try to open exact device stream
                    if (deviceId) {
                        try {
                            const s = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: false });
                            window.__forced_obs_stream = s;
                            const preview = document.querySelector('video') || document.querySelector('video[autoplay]');
                            if (preview) { try { preview.srcObject = s; preview.muted = true; preview.play().catch(()=>{}); } catch(e){} }
                            await sleep(900);
                        } catch (err) {
                            return { status: "getUserMedia_failed", error: String(err) };
                        }
                    } else {
                        // Request generic permission so labels appear, then enumerate
                        try {
                            const s2 = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                            window.__forced_obs_perm_stream = s2;
                            const preview2 = document.querySelector('video') || document.querySelector('video[autoplay]');
                            if (preview2) { try { preview2.srcObject = s2; preview2.muted = true; preview2.play().catch(()=>{}); } catch(e){} }
                            await sleep(900);
                        } catch (err) {
                            return { status: "perm_prompt_failed", error: String(err) };
                        }
                    }

                    // Try to open any camera menus so Zoom reveals options
                    try {
                        const toggles = Array.from(document.querySelectorAll('button,div,span'));
                        for (const t of toggles) {
                            const aria = (t.getAttribute && t.getAttribute('aria-label') || '').toLowerCase();
                            const txt = (t.innerText || '').toLowerCase();
                            if (aria.includes('camera') || /camera|video|preview/i.test(txt)) {
                                try { t.click(); await sleep(300); } catch(e){}
                            }
                        }
                    } catch(e){}

                    // Try to verify by checking active video element settings
                    try {
                        const vid = document.querySelector('video');
                        if (vid && vid.srcObject && vid.srcObject.getVideoTracks) {
                            const settings = vid.srcObject.getVideoTracks()[0].getSettings();
                            return { status: "verified", deviceId: settings.deviceId || null, settings };
                        }
                    } catch(e){}

                    // Enumerate devices and return camera list for verification
                    try {
                        const devs = await navigator.mediaDevices.enumerateDevices();
                        const cams = devs.filter(d => d.kind === 'videoinput');
                        return { status: "enumerated", cameras: cams.map(d => ({ label: d.label || '', deviceId: d.deviceId })) };
                    } catch(e){
                        return { status: "no_enumeration", error: String(e) };
                    }

                } catch(err){
                    return { status: "error", error: String(err) };
                }
            })();
        }
        """

        # Try several times; if obs_dev unknown, first call with None to reveal labels
        for attempt in range(6):
            try:
                device_id = obs_dev.get("deviceId") if obs_dev else None
                res = self.page.evaluate(camera_js, device_id)
                log.info("camera_select_attempt %d result: %s", attempt + 1, res)

                if isinstance(res, dict):
                    st = res.get("status")
                    if st == "verified":
                        # If verified and either matches our obs_dev or label indicates preferred name
                        vid = res.get("deviceId")
                        if obs_dev and vid and vid == obs_dev.get("deviceId"):
                            log.info("Verified OBS device active (deviceId match)")
                            return "verified_obs_active"
                        # accept verified even if obs_dev was not found earlier
                        log.info("Verified active device (settings): %s", res.get("settings"))
                        return "verified_other_device"
                    if st == "enumerated":
                        cams = res.get("cameras") or []
                        # update obs_dev if labels now reveal OBS
                        for c in cams:
                            if any(n in (c.get("label") or "").lower() for n in preferred_names):
                                log.info("Found OBS in enumerate: %s", c)
                                obs_dev = {"kind": "videoinput", "label": c.get("label"), "deviceId": c.get("deviceId")}
                                break
                        # if we still don't have obs_dev, try again after permission prompt
                    if st in ("getUserMedia_failed", "perm_prompt_failed"):
                        log.debug("getUserMedia/perm failed: %s", res.get("error"))
                # small wait before retrying
                self.page.wait_for_timeout(800)
            except Exception as e:
                log.exception("Camera selection evaluate failure: %s", e)
                time.sleep(0.5)

            # If we discovered obs_dev mid-loop, next iteration will pass its deviceId and try to verify

        # Final dump for debugging
        final = self._dump_detected_devices()
        log.warning("Failed to force OBS after attempts. Final devices: %s", final)
        return "failed_after_attempts"

    def _enable_video(self):
        """
        Force enable video using UI buttons and checkboxes.
        Returns True if any click happened.
        """
        video_js = r"""
        () => {
            try {
                const sleep = ms => new Promise(r => setTimeout(r, ms));
                // Try labels/checkboxes first (Join with video checkbox)
                const label = Array.from(document.querySelectorAll('label')).find(l => /join with video|with video/i.test(l.innerText || ''));
                if (label) {
                    try {
                        const cb = label.querySelector('input[type="checkbox"], input[type="radio"]') || document.querySelector('input[type="checkbox"]');
                        if (cb && !cb.checked) { cb.click(); return 'clicked_label_checkbox'; }
                    } catch(e){}
                }

                // Try buttons: "Join with Video", "Join", "Start Video", "Turn On Video"
                const els = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
                for (const e of els) {
                    const txt = (e.innerText || '').toLowerCase();
                    const aria = (e.getAttribute && (e.getAttribute('aria-label') || '').toLowerCase()) || '';
                    if (/join with video|join meeting with video|join meeting/i.test(txt) && /video/i.test(txt)) {
                        try { e.click(); return 'clicked_join_with_video_button'; } catch(e){}
                    }
                    if (/start video|turn on video|video on|join with video/i.test(txt) || /start video|turn on video/i.test(aria)) {
                        try { e.click(); return 'clicked_start_video'; } catch(e){}
                    }
                }

                // If nothing obvious, try clicking any "Join" button (Zoom may join with preview then present "Start Video")
                const joinBtn = els.find(e => /(^join$|join meeting|join now)/i.test((e.innerText||'').trim()));
                if (joinBtn) {
                    try { joinBtn.click(); return 'clicked_join_generic'; } catch(e){}
                }

                return false;
            } catch(err) {
                return false;
            }
        }
        """
        try:
            return bool(self.page.evaluate(video_js))
        except Exception:
            return False

    def join(self, meeting_id: str, password: str = None, display_name: str = "Avatar"):
        log.info(f"Joining meeting {meeting_id}")
        self.start_playwright()

        if not self.browser:
            self.browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--start-maximized",
                    "--autoplay-policy=no-user-gesture-required",
                    "--window-size=1920,1080"
                ]
            )

        try:
            if not self.context:
                self.context = self.browser.new_context(
                    permissions=["camera", "microphone"],
                    viewport={"width": 1920, "height": 1080}
                )
            self.page = self.context.new_page()

            join_url = f"https://zoom.us/wc/join/{meeting_id}"
            self.page.goto(join_url, timeout=60000)

            # wait a bit and then try to dump devices and force camera selection early
            self.page.wait_for_timeout(1500)
            try:
                cam_result = self._force_camera_selection()
                log.info("Initial camera selection: %s", cam_result)
            except Exception as e:
                log.warning("Camera selection raised: %s", e)

            # Fill name (if present)
            try:
                for selector in ("input[name='displayname']", "input[name='display_name']", "input[placeholder*='name' i]", "input[type='text']"):
                    try:
                        el = self.page.wait_for_selector(selector, timeout=1200)
                        if el:
                            el.fill(display_name)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Fill password (if present)
            if password:
                try:
                    for selector in ("input[type='password']", "input[placeholder*='passcode' i]", "input[aria-label*='passcode' i]"):
                        try:
                            el = self.page.wait_for_selector(selector, timeout=1200)
                            if el:
                                el.fill(password)
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

            # Ensure video on
            try:
                self._enable_video()
                self.page.wait_for_timeout(600)
            except Exception:
                pass

            # Click Join
            try:
                # try JS first
                js_click = """
                () => {
                    const els = Array.from(document.querySelectorAll('button, a, [role="button"]'));
                    for (const e of els) {
                        const t = (e.innerText || '').trim();
                        if (/^join( meeting)?$/i.test(t) || /join now/i.test(t) || /join with video/i.test(t)) {
                            try { e.click(); return t; } catch(e) {}
                        }
                    }
                    return null;
                }
                """
                r = self.page.evaluate(js_click)
                if not r:
                    # fallback to selectors
                    for sel in ("button:has-text('Join')", "button:has-text('Join Meeting')", "[role='button']:has-text('Join')"):
                        try:
                            btn = self.page.query_selector(sel)
                            if btn:
                                btn.click()
                                r = sel
                                break
                        except Exception:
                            continue
                log.info("Clicked join using: %s", r)
            except Exception as e:
                log.exception("Failed to click join: %s", e)
                # save debug info
                try:
                    self.page.screenshot(path="zoom_debug.png", full_page=True)
                    with open("zoom_debug.html", "w", encoding="utf-8") as f:
                        f.write(self.page.content())
                except Exception:
                    pass
                raise

            # Wait briefly for meeting to establish
            try:
                self.page.wait_for_selector("button:has-text('Leave')", timeout=20000)
            except TimeoutError:
                log.warning("Leave button not found after join timeout; continuing")

            self.in_meeting = True
            return True

        except Exception as e:
            log.exception("Join failed: %s", e)
            # try to close playwright cleanly
            try:
                self.stop_playwright()
            except Exception:
                pass
            raise

    def leave(self):
        """
        Click leave in UI and stop Playwright/browser.
        """
        log.info("Leaving meeting (ZoomClient.leave)")
        try:
            if self.page:
                try:
                    # try JS click leave
                    js_leave = """
                    () => {
                        const els = Array.from(document.querySelectorAll('button, a'));
                        for (const e of els) {
                            const t = (e.innerText || '').trim().toLowerCase();
                            if (t.includes('leave') || t.includes('end meeting')) {
                                try { e.click(); return t; } catch(e) {}
                            }
                        }
                        return null;
                    }
                    """
                    r = self.page.evaluate(js_leave)
                    log.info("leave click result: %s", r)
                except Exception:
                    pass
        finally:
            # ensure Playwright is stopped
            try:
                self.stop_playwright()
            except Exception:
                pass
            self.in_meeting = False
            log.info("Zoom client fully stopped")

    def wait_until_left(self, check_interval: float = 2.0, timeout: float = None) -> bool:
        """
        Block until the meeting ends or the client is removed/kicked.
        Returns True when the meeting is detected ended/kicked and cleanup is done.
        If timeout is provided and reached, returns False.
        """
        start = time.time()
        log.info("Waiting for meeting end / kick (no auto-leave)...")
        while True:
            if timeout and (time.time() - start) > timeout:
                log.warning("wait_until_left timed out after %.1fs", timeout)
                return False
            # if page no longer exists, consider it left
            if not self.page:
                log.info("Page closed - assuming left")
                self.in_meeting = False
                return True
            try:
                body = self.page.evaluate("() => (document && document.body && document.body.innerText) || ''")
            except Exception:
                # page.evaluate can fail if the browser dies; treat as left if browser closed
                log.debug("evaluate failed while waiting for meeting end; retrying")
                time.sleep(check_interval)
                continue
            text = (body or "").lower()
            # Common Zoom messages when removed or meeting ended
            if any(phrase in text for phrase in (
                "you have been removed",
                "you were removed",
                "you have been kicked",
                "you have been disconnected",
                "the meeting has ended",
                "this meeting has ended",
                "host has ended the meeting",
                "meeting ended"
            )):
                log.info("Detected meeting end/kick message in page text")
                try:
                    # attempt a polite leave/cleanup
                    self.stop_playwright()
                except Exception:
                    pass
                self.in_meeting = False
                return True
            # If the page shows the join/passcode form again, we likely left
            if "meeting passcode" in text and ("your name" in text or "your display name" in text or "join from your browser" in text):
                log.info("Detected returned-to-join-screen; meeting ended / left")
                try:
                    self.stop_playwright()
                except Exception:
                    pass
                self.in_meeting = False
                return True
            # Otherwise wait and check again
            time.sleep(check_interval)
