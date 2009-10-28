# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging

from twisted.internet import reactor
from afm.ui.glade import *
from afm.client import Client

log = logging.getLogger(__name__)

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


CON_STATUS, CON_NAME, CON_HOST, CON_PORT, CON_USER, CON_PASSWD = range(6)
ST_OFFLINE, ST_ONLINE, ST_CONNECTED = range(3)

class ConnectionsManager(GladeWidget):
    gladefile = 'ConnectionsManager.glade'

    def prepare_widget(self):
        self.window = self.gladeTree.get_widget('connection_manager')
        self.window.set_icon(AFM_LOGO_PIXBUF)

        self.conn_status_pixbuff = []
        for stock_id in (gtk.STOCK_NO, gtk.STOCK_YES, gtk.STOCK_CONNECT):
            self.conn_status_pixbuff.append(
                self.window.render_icon(stock_id, gtk.ICON_SIZE_MENU)
            )
        self.prepare_connections()

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

    def prepare_connections(self):
        self.conn_treeview = self.gladeTree.get_widget('connections_treeview')
        self._conn_create_model()
        self.conn_treeview.set_model(self.conn_model)
        self._conn_model_populate()
        self._conn_create_columns()

    def _conn_create_model(self):
        self.conn_model = gtk.ListStore(gobject.TYPE_INT,        # Status
                                        gobject.TYPE_STRING,     # Name
                                        gobject.TYPE_STRING,     # Hostname
                                        gobject.TYPE_INT,        # Port
                                        gobject.TYPE_STRING,     # Username)
                                        gobject.TYPE_STRING)     # Password


    def _conn_model_populate(self):
        for conn in self.parent.config.ui.servers.itervalues():
            self.conn_model.set(self.conn_model.append(),
                                CON_STATUS, ST_OFFLINE,
                                CON_NAME, conn.name,
                                CON_HOST, conn.hostname,
                                CON_PORT, conn.port,
                                CON_USER, conn.username,
                                CON_PASSWD, conn.password)
        reactor.callLater(1, self._conn_udpate_status)

    def _conn_create_columns(self):
        # Status
        renderer = gtk.CellRendererPixbuf()
        renderer.set_data("column", CON_STATUS)
        column = gtk.TreeViewColumn('Status', renderer)
        column.set_cell_data_func(renderer, self._conn_status_cell_render,
                                  CON_STATUS)
        self.conn_treeview.append_column(column)

        # Name
        renderer = gtk.CellRendererText()
        renderer.set_data("column", CON_NAME)
        column = gtk.TreeViewColumn('Name', renderer,
                                    text=CON_NAME,
                                    editable=False)
        column.set_expand(True)
        self.conn_treeview.append_column(column)

        # Hostname
        renderer = gtk.CellRendererText()
        renderer.set_data("column", CON_HOST)
        column = gtk.TreeViewColumn('Hostname', renderer,
                                    text=CON_HOST,
                                    editable=False)
        column.set_expand(True)
        self.conn_treeview.append_column(column)

        # Port
        renderer = gtk.CellRendererText()
        renderer.set_data("column", CON_PORT)
        column = gtk.TreeViewColumn('Port', renderer,
                                    text=CON_PORT,
                                    editable=False)
        self.conn_treeview.append_column(column)

        # Username
        renderer = gtk.CellRendererText()
        renderer.set_data("column", CON_USER)
        column = gtk.TreeViewColumn('Username', renderer,
                                    text=CON_USER,
                                    editable=False)
        column.set_expand(True)
        self.conn_treeview.append_column(column)

    def _conn_status_cell_render(self, column, cell, model, row, data):
        status = model[row][data]
        pixbuf = None
        if status in range(3):
            pixbuf = self.conn_status_pixbuff[status]
            cell.set_property("pixbuf", pixbuf)

    def _conn_udpate_status(self):
        for entry in self.conn_model:
            log.debug(entry[1])
            status = entry[CON_STATUS]
            name = entry[CON_NAME]
            host = entry[CON_HOST]
            port = entry[CON_PORT]
            user = entry[CON_USER]
            password = entry[CON_PASSWD]
            log.debug("Server connection Attempt: %s %s %s", host, port, user)
            client = Client()
            d = client.connect(host, port, user, password)
            def update_status(ret_status):
                print ret_status
                entry[CON_STATUS] = ret_status
            def failure(fail):
                log.debug("Failed to update status")
            d.addCallback(update_status).addErrback(failure)


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
