# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging
import gst

from twisted.internet import reactor
from afm import events, eventmanager

class BaseFailure(events.Event):
    def __init__(self, audio_source, message):
        self.source = audio_source
        self.message = message

class LWarning(BaseFailure):
    """ """

class LFailure(BaseFailure):
    """ """

class LOk(BaseFailure):
    """ """

class RWarning(BaseFailure):
    """ """

class RFailure(BaseFailure):
    """ """

class ROk(BaseFailure):
    """ """

class LRWarning(BaseFailure):
    """ """

class LRFailure(BaseFailure):
    """ """

class LROk(BaseFailure):
    """ """


class SilenceChecker(object):

    def __init__(self, min_tolerance=3000, max_tolerance=7000,
                 silence_level=-65):
        self.min_tolerance = min_tolerance
        self.max_tolerance = max_tolerance
        self.silence_level = silence_level #+ 45
        self.sLw = self.sRw = self.sLRw = None # silence (left, right, left+right) warning
        self.sLf = self.sRf = self.sLRf = None # silence (left, right, left+right) failure
        print 888, self.source.name, id(self)

    def __call__(self):
        return self.gst_element

    def __repr__(self):
        return '<%s for "%s">' % (self.__class__.__name__,
                                  self.source.name)

    def gst_element_factory_make(self, element_name):
        return gst.element_factory_make(
            element_name, '-'.join([element_name,
                                    ''.join(self.source.name.split())])
        )

    def prepare_test(self):
        # Level Check Element
        self.gst_element = self.gst_element_factory_make('level')
        self.gst_element.set_property('interval', 50000000)
        bus = self.source.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::element', self.check_bus_messages)

    def check_bus_messages(self, bus, message):
        if message.structure.get_name() == 'level':
            return self.handle_level_message(bus, message)

    def handle_level_message(self, bus, message):
        rms_L, rms_R = message.structure['rms']
        if rms_L < self.silence_level and rms_R < self.silence_level:
#            print 1, message.structure
            self.process_LR_failure(rms_L, rms_R)
        elif rms_L < self.silence_level:
#            print 888, self.source.name, id(self)
#            print 2, message.structure
            self.process_L_failure(rms_L, rms_R)
        elif rms_R < self.silence_level:
            self.process_R_failure(rms_L, rms_R)
        elif rms_L > self.silence_level and rms_R > self.silence_level:
            self.process_LR_ok(rms_L, rms_R)
        elif rms_L > self.silence_level:
            self.process_L_ok(rms_L, rms_R)
        elif rms_R > self.silence_level:
            self.process_R_ok(rms_L, rms_R)
        return True # Allow GST to keep processing

    def process_LR_failure(self, rms_L, rms_R):
        def warn():
            def fail():
                msg = "ERROR: Audio failure on both channels"
                eventmanager.emit(LRFailure(self, msg))
                self.sLRf.triggered = True

            self.sLRw.triggered = True
            msg = "WARN: Audio failure on both channels"
            eventmanager.emit(LRWarning(self, msg))
            self.sLRf = reactor.callLater(self.max_tolerance/1000, fail)
            self.sLRf.triggered = False


        def trigger():
            self.sLRw = reactor.callLater(self.min_tolerance/1000, warn)
            self.sLRw.triggered = False

        if not self.sLRw:
            trigger() # first time trigger
        elif self.sLRw and not self.sLRw.active() and not self.sLRw.triggered:
            trigger() # triggered before, but an ok has also happen since then

    def process_L_failure(self, rms_L, rms_R):
        def warn():
            def fail():
                msg = "ERROR: Audio failure on left channel"
                eventmanager.emit(LFailure(self, msg))
                self.sLf.triggered = True

            self.sLw.triggered = True
            msg = "WARN: Audio failure on left channel"
            eventmanager.emit(LWarning(self, msg))
            self.sLf = reactor.callLater(self.max_tolerance/1000, fail)
            self.sLf.triggered = False


        def trigger():
            self.sLw = reactor.callLater(self.min_tolerance/1000, warn)
            self.sLw.triggered = False

        if not self.sLw:
            trigger() # first time trigger
        elif self.sLw and not self.sLw.active() and not self.sLw.triggered:
            trigger() # triggered before, but an ok has also happen since then

    def process_R_failure(self, rms_L, rms_R):
        def warn():
            def fail():
                msg = "ERROR: Audio failure on right channel"
                eventmanager.emit(RFailure(self, msg))
                self.sRf.triggered = True

            self.sRw.triggered = True
            msg = "WARN: Audio failure on right channel"
            eventmanager.emit(RWarning(self, msg))
            self.sRf = reactor.callLater(self.max_tolerance/1000, fail)
            self.sRf.triggered = False


        def trigger():
            self.sRw = reactor.callLater(self.min_tolerance/1000, warn)
            self.sRw.triggered = False

        if not self.sRw:
            trigger() # first time trigger
        elif self.sRw and not self.sRw.active() and not self.sRw.triggered:
            trigger() # triggered before, but an ok has also happen since then

    def process_LR_ok(self, rms_L, rms_R):
        def ok():
            msg = "Audio resumed on both channels"
            eventmanager.emit(LROk(self, msg))

        if self.sLRw and self.sLRw.active():
            self.process_L_ok(rms_L, rms_R)
            self.process_R_ok(rms_L, rms_R)
            self.sLRw.cancel()
            self.sLRw = None
        elif self.sLRf and self.sLRf.active():
            self.process_L_ok(rms_L, rms_R)
            self.process_R_ok(rms_L, rms_R)
            self.sLRf.cancel()
            self.sLRf = None
            ok()
        elif getattr(self.sLRf, 'triggered', False):
            self.sLRf = self.sLRw = None
            self.process_L_ok(rms_L, rms_R)
            self.process_R_ok(rms_L, rms_R)
            ok()


    def process_L_ok(self, rms_L, rms_R):
        def ok():
            msg = "Audio resumed on left channel"
            eventmanager.emit(LOk(self, msg))

        if self.sLw and self.sLw.active():
            self.sLw.cancel()
            self.sLw = None
        elif self.sLf and self.sLf.active():
            self.sLf.cancel()
            self.sLf = None
            ok()
        elif getattr(self.sLf, 'triggered', False):
            self.sLf = self.sLw = None
            ok()

    def process_R_ok(self, rms_L, rms_R):
        def ok():
            msg = "Audio resumed on left channel"
            eventmanager.emit(ROk(self, msg))

        if self.sRw and self.sRw.active():
            self.sRw.cancel()
            self.sRw = None
        elif self.sRf and self.sRf.active():
            self.sRf.cancel()
            self.sRf = None
            ok()
        elif getattr(self.sRf, 'triggered', False):
            self.sRf = self.sRw = None
            ok()
