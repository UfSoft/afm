# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

from afm.client.glade import *

class ConnectionDetails(GladeWidget):
    gladefile = 'ConnectionDetails.glade'

    def prepare_widget(self):
        self.window = self.gladeTree.get_widget('connection_details')
        self.window.set_icon(AFM_LOGO_PIXBUF)
        self.name = self.gladeTree.get_widget('name')
        self.hostname = self.gladeTree.get_widget('hostname')
        self.port = self.gladeTree.get_widget('port')
        self.port.set_value(58848)
        self.username = self.gladeTree.get_widget('username')
        self.password = self.gladeTree.get_widget('password')

    def get_signal_handlers(self):
        return {
            'cancel_button_clicked_cb': lambda widget: self.window.hide(),
            'add_button_clicked_cb': self.add_button_clicked_cb,
        }

    def show(self, widget=None):
        self.window.show_all()

    def hide(self, widget=None):
        self.window.hide_all()

    def toggle(self, widget=None):
        if self.window.get_property("visible"):
            self.hide()
        else:
            self.show()

    def add_button_clicked_cb(self, widget):
        pass


class ConnectionsManager(GladeWidget):
    gladefile = 'ConnectionsManager.glade'

    def prepare_widget(self):
        self.window = self.gladeTree.get_widget('connection_manager')
        self.window.set_icon(AFM_LOGO_PIXBUF)

    def get_signal_handlers(self):
        return {
            'new_connection_button_clicked_cb': self.new_connection_button_clicked_cb,
            'delete_connection_button_clicked_cb': self.delete_connection_button_clicked_cb,
            'connect_button_clicked_cb': self.connect_button_clicked_cb,
            'close_button_clicked_cb': self.close_button_clicked_cb
        }

    def new_connection_button_clicked_cb(self, widget):
        connection_details = ConnectionDetails(self)
        connection_details.show()

    def delete_connection_button_clicked_cb(self, widget):
        pass

    def connect_button_clicked_cb(self, widget):
        pass

    def close_button_clicked_cb(self, widget):
        print 'close'
        self.hide()

    def load_connections(self):
        pass

    def show(self, widget=None):
        self.window.show_all()

    def hide(self, widget=None):
        self.window.hide_all()

    def toggle(self, widget=None):
        if self.window.get_property("visible"):
            self.hide()
        else:
            self.show()
