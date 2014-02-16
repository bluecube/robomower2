import time
import logging

class TimeElapsed:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.prev = time.time()

    def tick(self, frame_time):
        elapsed = time.time() - self.prev

        if frame_time > elapsed:
            time.sleep(frame_time - elapsed)
        else:
            self.logger.warning("Frame time too long (%d ms)", int(1000 * elapsed))

        t = time.time()
        elapsed_with_sleep = t - self.prev
        self.prev = t
        return elapsed_with_sleep, elapsed / frame_time

    def __call__(self):
        t = time.time()
        elapsed = t - self.prev
        self.prev = t
        return elapsed
