# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import gtk
import gtk.gdk
import gtk.glade
import gobject
from os.path import abspath, dirname, isfile, join

AFM_LOGO_PATH = join(dirname(__file__), 'static', 'logo.svg')
AFM_LOGO_PIXBUF = gtk.gdk.pixbuf_new_from_file(AFM_LOGO_PATH)
AFM_PAUSE_PATH = join(dirname(__file__), 'static', 'player_pause.png')
AFM_PLAY_PATH = join(dirname(__file__), 'static', 'player_play.png')

GLADE_FILES_BASE_PATH = join(dirname(__file__), 'glade')

if '_' not in __builtins__:
    def _(string):
        return string

class GladeWidget(gobject.GObject):
    gladefile = None

    def __init__(self, parent=None):
        if not self.gladefile:
            raise RuntimeError("You must define the 'gladefile' class attribute")
        self.__gobject_init__()
        self.parent = parent
        if not isfile(self.gladefile):
            gladefile = join(GLADE_FILES_BASE_PATH, self.gladefile)
            if not isfile(gladefile):
                raise RuntimeError("Could not find %r", self.gladefile)
            self.gladefile = gladefile
        self.gladeTree = gtk.glade.XML(self.gladefile)
        self.prepare_widget()
        self.gladeTree.signal_autoconnect(self.get_signal_handlers())
        self.window.set_icon_from_file(getattr(self, 'icon_path',
                                               AFM_LOGO_PATH))

    def get_signal_handlers(self):
        return {}

    def prepare_widget(self):
        pass

    def get_property(self, name):
        return self.window.get_property(name)
