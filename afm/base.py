# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging
from twisted.python.log import PythonLoggingObserver
from afm.logger import Logging
from afm.config import Configuration

class BaseApplication(object):
    def __init__(self, parsed_options):
        self.opts = parsed_options
        self.setup_logging()
        self.log = logging.getLogger(self.__class__.__module__)
        self.config = Configuration(self.opts['config-dir'])
        self.load_config()
        self.prepare_application()

    def prepare_application(self):
        raise NotImplementedError("You need to override this method")

    def load_config(self):
        raise NotImplementedError("You need to override this method")

    def setup_logging(self):
        if logging.getLoggerClass() is Logging:
            return
        log = logging.getLogger('afm')
        log.setLevel(self.opts['logging_level'])
        if self.opts['logfile']:
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                self.opts['logfile'],
                maxBytes=1*1024*1024,   # 1 MB
                backupCount=5,
                encoding='utf-8'
            )
        else:
            handler = logging.StreamHandler()

        handler.setLevel(self.opts['logging_level'])
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] [%(name)-15s] %(message)s",
            "%H:%M:%S"
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)

        log = logging.getLogger('twisted')
        log.setLevel(self.opts['logging_level'])
        log.addHandler(handler)
        logging.setLoggerClass(Logging)

        twisted_logging = PythonLoggingObserver('twisted')
        twisted_logging.start()
