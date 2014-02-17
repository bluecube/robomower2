import datetime
import logging
import os.path

class DataLogger:
    logger = logging.getLogger(__name__)

    def __init__(self, directory = "."):
        self._directory = directory
        self.start()

    def start(self):
        i = 1
        while True:
            filename = "robomower-recording-{}-{}.txt".format(datetime.date.today().isoformat(), i)
            filename = os.path.join(self._directory, filename)
            try:
                self._f = open(filename, "xt")
            except FileExistsError:
                i += 1
            else:
                self.logger.info("Writing to {}".format(filename))
                break

    def restart(self):
        self.stop()
        self.start()

    def stop(self):
        self._f.close()

    def write(self, *args):
        print(",".join(repr(x) for x in args), file=self._f)

