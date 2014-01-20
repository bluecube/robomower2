import time
import logging

class TimeElapsed:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.prev = time.time()

    def tick(self, frame_time):
        elapsed = self.prev - time.time() + 0.0
        # The constant accounts for the time spent not sleeping between the two time.time()
        # calls in this function

        if frame_time > elapsed:
            time.sleep(frame_time - elapsed)
        else:
            self.logger.warning("Frame time too long (%d ms)", int(1000 * elapsed))

        self.prev = time.time()
        return elapsed / frame_time

    def __call__(self):
        t = time.time()
        elapsed = t - self.prev
        self.prev = t
        return elapsed
