# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import gtk
import webbrowser
from afm.client.glade import AFM_LOGO_PIXBUF, _

import irssinotifier

class AboutDialog(object):
    """The about dialog."""
    def __init__(self, parent=None):
        """Creates a new about dialog and configures it."""
        self.parent = parent
        gtk.about_dialog_set_url_hook(self.open_link)
        self.dialog = gtk.AboutDialog()
        self.dialog.set_name(_('Audio Failure Monitor'))
        self.dialog.set_version(irssinotifier.__version__)
        # TRANSLATOR: No need to translate copyright
        self.dialog.set_copyright(_('2009 © UfSoft.org'))
        self.dialog.set_comments(_('Audio Failures Monitor'))
        self.dialog.set_license(irssinotifier.__license_text__)
        self.dialog.set_website(irssinotifier.__url__)
        self.dialog.set_website_label(_('Go To Development Site'))
        self.dialog.set_authors([
            'Pedro Algarvio <ufs@ufsoft.org>'
        ])
        self.dialog.set_translator_credits(
            'pt_PT: Pedro Algarvio <ufs@ufsoft.org>'
        )
        self.dialog.set_logo(AFM_LOGO_PIXBUF)
        self.dialog.set_icon(AFM_LOGO_PIXBUF)

        self.dialog.connect("response", lambda d, r: self.hide())

    def open_link(self, dialog, link, user_data=None):
        webbrowser.open(link, new=True, autoraise=True)

    def show(self):
        self.dialog.show_all()

    def hide(self):
        self.dialog.hide_all()
