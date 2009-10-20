# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging

from twisted.application import internet
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.python.log import PythonLoggingObserver
from twisted.spread import pb
from zope.interface import implements

from afm import eventmanager, events

class AFMAvatar(pb.Avatar):
    pass

class ServiceRealm(object):
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective in interfaces:
            a = AFMAvatar()
            return pb.IPerspective, a, lambda : None
        else:
            raise NotImplementedError("no interface")

class Application(object):

    def __init__(self, parsed_options):
        self.opts = parsed_options
        self.setup_logging()
        self.load_config()
        self.setup_gstreamer()
        eventmanager.register_event_handler("ApplicationLoaded",
                                            self.load_sources)


    def setup_logging(self):

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

        from afm.logger import Logging
        logging.setLoggerClass(Logging)

        twisted_logging = PythonLoggingObserver('twisted')
        twisted_logging.start()

    def load_config(self):
        from afm.config import Configuration
        self.config = Configuration(self.opts['config-dir'])

    def setup_gstreamer(self):
        import gobject
        gobject.threads_init()
        import pygst
        pygst.require("0.10")
        import gst
#        import pygtk
#        pygtk.require('2.0')
#        import gtk
        # GST Debugging
#        gst.debug_set_active(True)
#        gst.debug_set_default_threshold(gst.LEVEL_WARNING)
#        gst.debug_set_colored(True)


    def get_service(self):
        from afm import eventmanager
        portal = Portal(ServiceRealm())
        checker = InMemoryUsernamePasswordDatabaseDontUse()
        for username, password in self.config.users.iteritems():
            checker.addUser(username, password)
        portal.registerChecker(checker)
        from twisted.internet import reactor
        eventmanager.emit(events.ApplicationLoaded())
        return internet.TCPServer(self.config.core.port,
                                  pb.PBServerFactory(portal))

    def load_sources(self):
        n = 0
        from afm.sources import Source
        available_sources = self.config.sources.keys()
        available_sources.sort()
        for source_name in available_sources:
            source_config = self.config.sources[source_name]
            logging.getLogger(__name__).debug(source_config)
            source = Source(source_config)
            source.prepare_source()
            if n >= 1:
                break
            n+=1

