# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging
from twisted.internet import defer

log = logging.getLogger(__name__)

class EventManager(object):
    def __init__(self):
        self.handlers = {}

    def emit(self, event):
        log.debug("Emmiting event %r with args %r", event.name, event.args)
        if hasattr(event, 'source'):
            log.debug("Source %r id %r", event.source, id(event.source))
        if event.name in self.handlers:
            for handler in self.handlers[event.name]:
                defer.maybeDeferred(handler, *event.args)

    def register_event_handler(self, event, handler):
        log.debug("Registering handler %r for event %r", handler, event)
        if event not in self.handlers:
            self.handlers[event] = []
        if handler not in self.handlers[event]:
            self.handlers[event].append(handler)

    def deregister_event_handler(self, event, handler):
        log.debug("De-Registering handler %r for event %r", handler, event)
        if event in self.handlers and handler in self.handlers[event]:
            self.handlers[event].remove(handler)

class Event(object):

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        obj._args = args
        obj._kwargs = kwargs
        return obj

    def _get_name(self):
        return self.__class__.__name__

    def _get_args(self):
        return list(getattr(self, '_args', []))

    def _get_kwargs(self):
        return getattr(self, '_kwargs', {})

    name = property(fget=_get_name)
    args = property(fget=_get_args)
    kwargs = property(fget=_get_kwargs)


class ApplicationLoaded(Event):
    """Fired when application is loaded"""

class SourceLoaded(Event):
    def __init__(self, source):
        self.source = source

class SourcePrepared(Event):
    def __init__(self, source):
        self.source = source
