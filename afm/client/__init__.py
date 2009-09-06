# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

try:
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
except AssertionError:
    print 'Failed to install GTK2Reactor'

import gobject
gobject.threads_init()

import pygst
pygst.require("0.10")
import gst

import pygtk
pygtk.require('2.0')
import gtk

# GST Debugging
gst.debug_set_active(True)
gst.debug_set_default_threshold(gst.LEVEL_WARNING)
gst.debug_set_colored(True)
