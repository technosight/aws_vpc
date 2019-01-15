import time

class Timer:

    def __init__(self, interval, timeout):
        self.count = 0
        self.interval = interval
        self.timeout = timeout
        self.max_count = self.timeout / self.interval

    def wait(self):
        self.count += 1
        if self.count > self.max_count:
            raise Exception('Timeout {} exceeded'.format(self.timeout))
        time.sleep(self.interval)