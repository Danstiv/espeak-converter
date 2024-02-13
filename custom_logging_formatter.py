import logging
import time


class Formatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_msec_format = "%s,%03d %s"

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        t1 = time.strftime("%H:%M:%S", ct)
        t2 = time.strftime("%Y-%m-%d", ct)
        s = self.default_msec_format % (t1, record.msecs, t2)
        return s
