# -*- coding: utf-8 -*-

import logging

from PyQt4.QtCore import QObject, pyqtSignal


class SignalEmitter (QObject):

    logged = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)

    # def emit_signal(self, msg):
    #     self.logged.emit(msg)


class LogHandler(logging.FileHandler, SignalEmitter):

    def __init__(self, filename):
        SignalEmitter.__init__(self)
        logging.FileHandler.__init__(self, filename)
        self.msg = None

    # def emit(self, record):
    #     super(LogHandler, self).emit(record)
    #     self.msg = self.format(record)
    #     super(LogHandler, self).emit_signal(self.msg)
