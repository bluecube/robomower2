import time
import logging

class TimeElapsed:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.prev = time.time()

    def tick(self, frame_time):
        elapsed = self()
        elapsed2 = elapsed + 0.01
        if frame_time > elapsed2:
            time.sleep(frame_time - elapsed2)
        elif frame_time > elapsed:
            pass
        else:
            self.logger.warning("Frame time too long (%d ms)", int(1000 * elapsed))

    def __call__(self):
        t = time.time()
        elapsed = t - self.prev
        self.prev = t
        return elapsed
