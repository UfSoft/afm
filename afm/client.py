# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging

from twisted.cred.credentials import UsernamePassword, Anonymous
from twisted.internet import defer, reactor
from twisted.spread import pb

log = logging.getLogger(__name__)

class Client(object):

    def connect(self, host, port, user, passwd):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        factory = pb.PBClientFactory()
        reactor.connectTCP(host, port, factory)
        d = defer.maybeDeferred(factory.login, UsernamePassword(user, passwd))
        def logged_in(remote_ref):
            log.debug("111: %s", remote_ref.__dict__)
            log.debug(remote_ref.broker.callRemote('version'))
            factory.getRootObject().addCallbacks(self.__conn_success,
                                                 self.__conn_failure)
#            d.addCallback(factory.getRootObject).addCallbacks(self.__conn_success,
#                                                              self.__conn_failure)
        d.addCallback(logged_in)
        return d

    def __conn_success(self, perspective):
        log.debug("Connected to %s@%s:%s!!!!", self.user, self.host, self.port)
        self.server_status = 1
        self.server = perspective
        self.get_server_version()
        return 1

    def __conn_failure(self, failure):
        log.debug(failure)
        log.debug("No Connection to %s@%s:%s!!!!", self.user, self.host, self.port)
        self.server_status = 0
        return 0

    def get_server_version(self):
        d = self.server.callRemote('version')
        def success(v):
            print 123, v
        def fail(f):
            print 321, f
        d.addCallbacks(success, fail)

