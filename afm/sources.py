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
from afm import eventmanager, events
log = logging.getLogger(__name__)

class Source(object):
    def __init__(self, source_config):
        source_config.source = self
        self.config = source_config
        self.name = self.config.name
        self.uri = self.config.uri
        eventmanager.register_event_handler("SourcePrepared",
                                            self.start)

    def prepare_source(self):
        self.pipeline = gst.Pipeline("%s-pipeline" % ''.join(self.name.split()))
        self.bus = self.pipeline.get_bus()

        self.source = gst.element_factory_make('uridecodebin')
        self.source.set_property('uri', self.uri)
        self.sourcecaps = gst.Caps()
        self.sourcecaps.append_structure(gst.Structure("audio/x-raw-float"))
        self.sourcecaps.append_structure(gst.Structure("audio/x-raw-int"))
        self.source.set_property("caps", self.sourcecaps)

        self.pipeline.add(self.source)
        self.source.connect("pad-added", self.on_pad_added)
        self.source.connect("no-more-pads", self.on_no_more_pads)
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.source.set_state(gst.STATE_PAUSED)
        eventmanager.emit(events.SourcePrepared(self))


    def connect_signal_to_tests(self, *args, **kwargs):
        for test in self.tests:
            test.connect(*args, **kwargs)

    def on_no_more_pads(self, dbin):
        reactor.callLater(0, self.pipeline.set_state, gst.STATE_PLAYING)

    def gst_element_factory_make(self, element_name, n=None):
        return gst.element_factory_make(
            element_name, '-'.join([n and '-'.join(element_name, n) or element_name,
                                    ''.join(self.name.split())])
        )

    def on_pad_added(self, dbin, sink_pad):
        c = sink_pad.get_caps().to_string()
        if c.startswith("audio/"):
            self.convert = self.gst_element_factory_make('audioconvert')
            self.pipeline.add(self.convert)
            self.resample = self.gst_element_factory_make('audioresample')
            self.pipeline.add(self.resample)

#            self.sink = self.gst_element_factory_make('alsasink')
            self.sink = self.gst_element_factory_make('fakesink')
            self.pipeline.add(self.sink)

            self.source.link(self.convert)
            self.convert.link(self.resample)

            # TESTS
            last_test = self.resample
            self.tests = []
            for idx, test in enumerate(self.config.get_tests(self)):
                test.prepare_test()
                self.pipeline.add(test())
                self.tests.append(test)
                last_test.link(test())
                last_test = test()
                queue = self.gst_element_factory_make('queue', n=idx)
                self.pipeline.add(queue)
                last_test.link(queue)
                last_test = queue
                queue.set_state(gst.STATE_PAUSED)
                test().set_state(gst.STATE_PAUSED)
            last_test.link(self.sink)

            self.convert.set_state(gst.STATE_PAUSED)
            self.resample.set_state(gst.STATE_PAUSED)
            self.sink.set_state(gst.STATE_PAUSED)
        return True

    def __call__(self):
        return self.source

    def __repr__(self):
        return '<%s name="%s">' % (self.__class__.__name__, self.name)

    def start(self, source):
        if source is self:
            self.pipeline.set_state(gst.STATE_PLAYING)

    def stop(self, source):
        if source is self:
            self.pipeline.set_state(gst.STATE_NULL)

