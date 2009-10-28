# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import sys
import logging
from os.path import abspath, basename, expanduser, isdir, join
from twisted.application import app
from twisted.application.service import Application, IServiceCollection

from twisted.python import usage
from twisted.python.log import PythonLoggingObserver
from twisted.spread import pb
from zope.interface import implements

from afm import __summary__, __version__, application, events


class DaemonOptions(usage.Options):
    longdesc = __summary__

    optFlags = [
        ['quiet', 'q', 'Be quiet. No output.'],
        ['debug', 'd', 'Debug output'],
        ['no-color', 'C', 'No color debuging output']
    ]

    optParameters = [
        ['config-dir', 'c', '~/.afm', "Configuration Directory"],
        ['logfile', 'l', None, "Logfile path"]
    ]

    def __init__(self):
        usage.Options.__init__(self)
        self.opts['logging_level'] = logging.INFO

    def opt_version(self):
        """Show version"""
        print "%s - %s" % (basename(sys.argv[0]), __version__)
    opt_v = opt_version

    def opt_help(self):
        """Show this help message"""
        super(Options, self).opt_help()
    opt_h = opt_help

    def opt_quiet(self):
        self.opts['logging_level'] = logging.FATAL
        self.opts['quiet'] = True

    def opt_debug(self):
        self.opts['logging_level'] = logging.DEBUG
        self.opts['debug'] = True

    def opt_no_color(self):
        self.opts['no-color'] = True

    def opt_config_dir(self, configdir):
        self.opts['config-dir'] = abspath(expanduser(configdir))

    def opt_logfile(self, filepath):
        self.opts['logfile'] = abspath(expanduser(filepath))

    def postOptions(self):
        if not isdir(self.opts['config-dir']):
            self.opt_config_dir(self.opts['config-dir'])
        if self.opts['quiet'] and self.opts['debug']:
            print "ERROR: Only pass one of '--debug' or '--quiet', not both."
            self.opt_help()
            sys.exit(1)

    def getService(self):
        from afm.app import Application
        application = Application(self.opts)
        return application.get_service()

class ClientOptions(DaemonOptions):

    def getService(self):
        from afm.client.app import Application
        application = Application(self.opts)
        return application.get_service()

def daemon():
    from twisted.internet import glib2reactor
    glib2reactor.install()
    from twisted.internet import reactor

    main_app = Application("Audio Failure Monitor") #, uid, gid)

    services = IServiceCollection(main_app)
    options = DaemonOptions()
    options.parseOptions()
    service = options.getService()
    service.setServiceParent(services)

    app.startApplication(main_app, False)

    reactor.addSystemEventTrigger('before', 'shutdown',
                                  logging.getLogger(__name__).info,
                                  'Stopping AFM')

    logging.getLogger(__name__).info("AFM Started")
    try:
        reactor.run()
    except KeyboardInterrupt:
        reactor.stop()

def client():
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
    from twisted.internet import reactor
#    import gobject
#    reactor.callWhenRunning(gobject.threads_init)
#    gobject.threads_init()

    options = ClientOptions()
    options.parseOptions()

    from afm.ui.app import Application
    app = Application(options)

    reactor.addSystemEventTrigger('before', 'shutdown',
                                  logging.getLogger(__name__).info,
                                  'Stopping AFM Client')

    logging.getLogger(__name__).info("AFM Client Started")
    try:
        reactor.run()
    except KeyboardInterrupt:
        reactor.stop()
    except:
        raise
        from twisted.python import log
        log.err()

