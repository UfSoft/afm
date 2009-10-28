# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging

from twisted.application import internet
from twisted.python.log import PythonLoggingObserver
from foolscap.api import Referenceable, Tub, UnauthenticatedTub

from afm import eventmanager, events, __version__

class InfoTub(Referenceable):

    def __init__(self):
        Referenceable.__init__(self)
        eventmanager.register_event_handler("CoreUrlGenerated",
                                            self._update_core_url)

    def remote_version(self):
        return __version__

    def remote_uri(self):
        return self.coreurl

    def _update_core_url(self, coreurl):
        self.coreurl = coreurl


class Application(object):

    def __init__(self, parsed_options):
        self.opts = parsed_options
        eventmanager.register_event_handler("ApplicationLoaded",
                                            self.load_sources)
        self.setup_logging()
        self.load_config()
        self.setup_tubs()
        self.setup_gstreamer()
        eventmanager.emit(events.ApplicationLoaded())


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
        self.config.load_core_config()

    def setup_tubs(self):
        self.infotub = UnauthenticatedTub()
        self.infotub.listenOn('tcp:%d' % self.config.core.info_port)
        self.infotub.setLocation("localhost:%d" % self.config.core.info_port)
#        self.infotub.setLocationAutomatically()
        info_server = InfoTub()
        info_url = self.infotub.registerReference(info_server, 'info')
        logging.getLogger(__name__).debug('Info url: %s', info_url)
#        self.infotub.startService()
        self.coretub = Tub()
        self.coretub.listenOn('tcp:%d' % (self.config.core.core_port))
        self.coretub.setLocation("localhost:%d" % (self.config.core.core_port))
#        self.coretub.setLocationAutomatically()
        core_info_url = self.coretub.registerReference(info_server, 'info')
        logging.getLogger(__name__).debug('Core Info url: %s', core_info_url)
        eventmanager.emit(events.CoreUrlGenerated(core_info_url))
#        self.coretub.startService()

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
#        gst.debug_set_default_threshold(gst.LEVEL_INFO)
#        gst.debug_set_colored(True)


    def get_service(self):
        return internet.TCPServer(self.config.core.port, factory)

    def load_sources(self):
        from afm.sources import Source
        log = logging.getLogger(__name__)
        available_sources = self.config.sources.keys()
        available_sources.sort()
        for source_name in available_sources:
            source_config = self.config.sources[source_name]
            if not source_config.active:
                log.debug("Skipping %s. Not Active.", source_config)
                continue
            log.debug("%s active. Loading...", source_config)
            source = Source(source_config)
            source.prepare_source()

