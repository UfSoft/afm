# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging


from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import IUsernamePassword, IUsernameHashedPassword
from twisted.cred.error import UnauthorizedLogin
from twisted.cred.portal import IRealm
from twisted.internet import defer
from twisted.spread import pb
from zope.interface import implements, Interface

log = logging.getLogger(__name__)

CRED_ANONYM, CRED_REGULAR, CRED_ADMIN = range(3)

class IProtocolUser(Interface):
    def get_privilages():
        """Return a list of privileges this user has"""

    def logout():
        """Cleanup per-login resources allocated to this avatar"""

class AnonymousUser(pb.Avatar):
    implements(IProtocolUser)

    def get_privileges(self):
        return [CRED_ANONYM]

    def logout(self):
        log.debug("Cleaning up anonymous user resources")

    def remote_version(self):
        return '0.1 - R'
    def perspective_version(self):
        return '0.1 - P'

class RegularUser(pb.Avatar):
    implements(IProtocolUser)

    def get_privileges(self):
        return [CRED_ANONYM, CRED_REGULAR]

    def logout(self):
        log.debug("Cleaning up regular user resources")

    def remote_version(self):
        return '0.1 - R'
    def perspective_version(self):
        return '0.1 - P'

class Administrator(pb.Avatar):
    implements(IProtocolUser)

    def get_privileges(self):
        return [CRED_ANONYM, CRED_REGULAR, CRED_ADMIN]

    def logout(self):
        log.debug("Cleaning up administrator resources")

    def remote_version(self):
        return '0.1 - R'
    def perspective_version(self):
        return '0.1 - P'

class AFMChecker(object):
    credentialInterfaces = IUsernamePassword, IUsernameHashedPassword
    implements(ICredentialsChecker)

    def requestAvatarId(self, credentials):
        log.debug("Login attempt of user %s", credentials.username)
        if credentials.username in self.app.config.users:
            userconfig = self.app.config.users[credentials.username]
            d = defer.maybeDeferred(
                credentials.checkPassword, userconfig.password
            ).addCallback(self._cbPasswordMatch, userconfig)
            return d
        return defer.fail(UnauthorizedLogin("User not known"))

    def _cbPasswordMatch(self, matched, username):
        if matched:
            return username
        return defer.fail(UnauthorizedLogin("Authentication failed. Password "
                                            "does not match"))

    def authenticate(self, credentials):
        print credentials.__dict__
        return defer.fail(UnauthorizedLogin("unable to verify password"))

class ServiceRealm(object):
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective in interfaces:
            logging.getLogger(__name__).debug("My realm: %s %s", avatarId, mind)
            if avatarId.level == 0:
                avatar = AnonymousUser()
            elif avatarId.level == 1:
                avatar = RegularUser()
            elif avatarId.level == 2:
                avatar = Administrator()
            return pb.IPerspective, avatar, avatar.logout
        else:
            raise NotImplementedError("no interface")
