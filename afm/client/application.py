# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import gtk
import gtk.gdk
import gobject

import pango

from afm.client.about import AboutDialog
from afm.client.glade import GladeWidget, AFM_LOGO_PATH
from twisted.internet import defer

class Splash(GladeWidget):
    gladefile = 'SplashScreen.glade'
    steps = {}
    minShow = 3
    canClose = finished = False

    def __init__(self, parent=None, type=gtk.WINDOW_TOPLEVEL):
        GladeWidget.__init__(self, parent)
        def setCanClose():
            self.canClose=True
        reactor.callLater(self.minShow, setCanClose)

    def destroy(self):
        if not self.canClose:
            reactor.callLater(1, self.destroy)
            return
        elif not self.finished:
            reactor.callLater(1, self.destroy)
            return
        self.window.destroy()

    def prepare_widget(self):
        self.window = self.gladeTree.get_widget('mainWindow')
        self.logo = self.gladeTree.get_widget('logo')
        self.logo.set_from_file(AFM_LOGO_PATH)
        self.progress = self.gladeTree.get_widget('progressbar')
        self.copyright = self.gladeTree.get_widget('copyright')
        copyfont = pango.FontDescription()
        copyfont.set_size(7*pango.SCALE)
        self.copyright.modify_font(copyfont)
        self.window.realize()
        self.window.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
        # needed because the window_type hint above does not work on Win32 :-/
        self.window.set_decorated(False)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.show()

    def show(self):
        self.window.show_all()

    def hide(self):
        self.window.hide_all()

    def register_step(self, function, *args, **kwargs):
        print 'registering', function, args, kwargs
        self.steps[len(self.steps)] = (function, args, kwargs)

    def run(self):
        step_count = len(self.steps)
        step_fractions = [float(n)/(step_count-1) for n in range(step_count)]

        def errback(failure):
            print 'ERROR', failure
            raise failure

        for step_num, step_fraction in zip(range(step_count), step_fractions):
            func, args, kwargs = self.steps[step_num]
            d = defer.maybeDeferred(func, *args, **kwargs)
            d.addErrback(errback)
            d.addCallback(lambda d: self.progress.set_fraction(step_fraction))
            d.addErrback(errback)
        self.finished = True
#        reactor.callLater(0, self.progress.hide)

class Application(gobject.GObject):

    _progress_provider = []
    def progress_provider(func, container=_progress_provider):
        container.append(func)
        from functools import wraps  # use this to preserve function signatures and docstrings
        @wraps(func)
        def wrapped(cls, *args, **kwargs):
            return func(cls, *args, **kwargs)
        return wrapped

    def __init__(self):
        self.__gobject_init__()

        self.splash = Splash(parent=self)
        self.register_steps()
#        self.splash.register_step(self.setup_about_dialog)
#        self.splash.register_step(self.setup_trayicon)
#        self.splash.register_step(self.setup_trayicon_menu)

#        r = open('/dev/urandom', 'r')
#        for n in range(12):
#            self.splash.register_step(r.read, 524288)
        reactor.callInThread(self.startup)

    def register_steps(self):
        for step in self._progress_provider:
            self.splash.register_step(step, self)

    def startup(self):
        d = defer.maybeDeferred(self.splash.run)
        d.addCallback(lambda *x: self.splash.destroy())
        return d

    @progress_provider
    def setup_about_dialog(self):
        self.about_dialog = AboutDialog(self)

    @progress_provider
    def setup_trayicon(self):
        tray_icon = gtk.StatusIcon()
        tray_icon.set_from_file(AFM_LOGO_PATH)
        tray_icon.connect('popup-menu', self.popup_menu)
        tray_icon.set_tooltip('Audio Failure Monitor')
        tray_icon.set_visible(True)
        self.tray_icon = tray_icon

    @progress_provider
    def setup_trayicon_menu(self):
        """Creates the menu obtained when right-clicking the tray icon."""
        about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        about.connect_object('activate', self.show_about, 'about')
        about.show()

        prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
#        prefs.connect_object('activate', self.prefs, 'prefs')
        prefs.show()

        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit.connect_object('activate', self.exit, 'quit')
        quit.show()

        menu = gtk.Menu()
        menu.append(about)
        menu.append(prefs)
        menu.append(quit)
        self.tray_icon_menu = menu

    def popup_menu(self, status_icon, button, activate_time):
        """Handler to be called when the tray icon is right-clicked.

        Arguments:

            status_icon -- The tray icon object.
            button -- The button pressed.
            activate_time -- The time of the event.

        Shows the menu.
        """
        self.tray_icon_menu.popup(None, None,
                                  gtk.status_icon_position_menu, button,
                                  activate_time, status_icon)

    def show_about(self, widget):
        """Shows the about dialog."""
        self.about_dialog.show()

    def exit(self, widget):
        """Exits the application."""
        self.tray_icon.set_visible(False)
        reactor.stop()

if __name__ == '__main__':
    from twisted.internet import defer, reactor

    app = Application()
    reactor.run()
