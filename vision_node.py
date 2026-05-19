import asyncio
import mss
import cv2
import numpy as np
from livekit import rtc

class OpticalCortex:
    def __init__(self):
        # Setting up a 360p WebRTC Video Source (matching our lower res output)
        self.source = rtc.VideoSource(640, 360)
        self.track = rtc.LocalVideoTrack.create_video_track("desktop_vision_feed", self.source)
        self.sct = mss.mss()

    async def stream_monitor(self):
        print("[OPTICAL CORTEX]: Motion-adaptive vision enabled.")
        monitor = self.sct.monitors[1] if len(self.sct.monitors) > 1 else self.sct.monitors[0]
        prev_frame = None

        while True:
            try:
                sct_img = self.sct.grab(monitor)
                img = np.array(sct_img)
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                img_gray = cv2.resize(img_gray, (640, 360)) # Lower res to save bandwidth

                # Motion detection: Only send if screen changed by > 5%
                if prev_frame is not None:
                    diff = cv2.absdiff(img_gray, prev_frame)
                    non_zero = cv2.countNonZero(diff)
                    if non_zero < (img_gray.size * 0.05): # Less than 5% change
                        await asyncio.sleep(2.0) # Wait longer if screen is static
                        continue

                prev_frame = img_gray
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
                img = cv2.resize(img, (640, 360))

                frame = rtc.VideoFrame(img.shape[1], img.shape[0], rtc.VideoBufferType.RGBA, img.tobytes())
                self.source.capture_frame(frame)
                await asyncio.sleep(1.0)
            except Exception as e:
                print(f"[VISION ERROR]: {str(e)}")
                await asyncio.sleep(5)