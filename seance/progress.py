import sys
import datetime

class Progress(object) :
    def __init__(self, title, total) :
        self.title = title
        self.total = float(total)
        self.current = 0
        self.start_time = None

    def print_out(self) :
        print >> sys.stderr, "\r[%s] %d / %d " % (self.title, self.current, self.total),

    def percent(self) :
        return self.current / self.total

    def time(self) :
        seconds = (datetime.datetime.now() - self.start_time).seconds
        return "%d second%s" % (seconds, "" if seconds == 1 else "s")

    def increment(self) :
        self.current += 1
        self.print_out()

    def start(self) :
        self.start_time = datetime.datetime.now()
        print >> sys.stderr, ""
        self.print_out()

    def end(self) :
        print >> sys.stderr, "\r[%s] finished in %s\n" % (self.title, self.time())

