# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging

from twisted.internet import defer, task
from foolscap.api import Tub
from afm.ui.glade import *
from afm import eventmanager, events

log = logging.getLogger(__name__)

class DaemonStarted(events.Event):
    pass

class DaemonStopped(events.Event):
    pass

class ConnectionDetails(GladeWidget):
    gladefile = 'ConnectionDetails.glade'

    def prepare_widget(self):
        self.window = self.gladeTree.get_widget('connection_details')
        self.window.set_icon(AFM_LOGO_PIXBUF)
        self.name = self.gladeTree.get_widget('name')
        self.uri = self.gladeTree.get_widget('uri')
        self.apply_button = self.gladeTree.get_widget('apply_button')
        self.apply_button.set_property("visible", False)
        self.add_button = self.gladeTree.get_widget('add_button')

    def get_signal_handlers(self):
        return {
            'cancel_button_clicked_cb': lambda widget: self.window.hide(),
            'add_button_clicked_cb': self.add_button_clicked_cb,
            'apply_button_clicked_cb': self.apply_button_clicked_cb,
        }

    def show(self, widget=None):
        self.new_connection()

    def new_connection(self):
        self.window.show_all()
        self.apply_button.set_property("visible", False)

    def edit_connection(self):
        self.window.show_all()
        self.apply_button.set_property("visible", True)
        self.add_button.set_property("visible", False)

    def hide(self, widget=None):
        self.window.hide_all()

    def toggle(self, widget=None):
        if self.window.get_property("visible"):
            self.hide()
        else:
            self.show()

    def add_button_clicked_cb(self, widget):
        pass

    def apply_button_clicked_cb(self, widget):
        pass


CON_STATUS, CON_NAME, CON_URI, CON_VERSION, CON_CORE_URI = range(5)
ST_OFFLINE, ST_ONLINE, ST_CONNECTED = range(3)

class ConnectionsManager(GladeWidget):
    gladefile = 'ConnectionsManager.glade'
    connection_update_interval = 10
    selected_connection_iter = None
    daemon_running = None

    def prepare_widget(self):
        eventmanager.register_event_handler("DaemonStarted",
                                            self.on_event_daemon_started)
        self.window = self.gladeTree.get_widget('connection_manager')
        self.window.set_icon(AFM_LOGO_PIXBUF)
        self.connect_button = self.gladeTree.get_widget('connect_button')
        self.edit_connection_button = self.gladeTree.get_widget(
            'edit_connection_button'
        )
        self.delete_connection_button = self.gladeTree.get_widget(
            'delete_connection_button'
        )
        self.start_service_button = self.gladeTree.get_widget(
            'start_service_button'
        )

        self.conn_status_pixbuff = []
        for stock_id in (gtk.STOCK_NO, gtk.STOCK_YES, gtk.STOCK_CONNECT):
            self.conn_status_pixbuff.append(
                self.window.render_icon(stock_id, gtk.ICON_SIZE_MENU)
            )
        self.conn_status_task = task.LoopingCall(self._conn_update_details)
        self.prepare_connections()
        conn_treeview_selection = self.conn_treeview.get_selection()
        conn_treeview_selection.connect("changed",
                                        self.conn_treeview_selection_changed)
        self.conn_treeview_selection = conn_treeview_selection

    def on_event_daemon_started(self):
        self.start_service_button.set_property('sensitive', False)
        self.connect_button.set_property('sensitive', True)

    def on_event_daemon_stopped(self):
        pass


    def get_signal_handlers(self):
        return {
            'new_connection_button_clicked_cb': self.new_connection_button_clicked_cb,
            'delete_connection_button_clicked_cb': self.delete_connection_button_clicked_cb,
            'connect_button_clicked_cb': self.connect_button_clicked_cb,
            'close_button_clicked_cb': self.close_button_clicked_cb,
            'start_service_button_clicked_cb': self.start_service_button_clicked_cb,
        }

    def new_connection_button_clicked_cb(self, widget):
        connection_details = ConnectionDetails(self)
        connection_details.show()

    def delete_connection_button_clicked_cb(self, widget):
        log.debug("Delete connection: %s",
                  self.conn_model.get(self.selected_connection_iter, CON_NAME))
        self.conn_model.remove(self.selected_connection_iter)
        # XXX: Delete connection configuration from config file

    @defer.inlineCallbacks
    def connect_button_clicked_cb(self, widget):
        log.debug("Trying to connect to Core: %s",
                  self.conn_model.get(self.selected_connection_iter, CON_NAME)[0])
        uri = yield self.conn_model.get(self.selected_connection_iter, CON_CORE_URI)[0]
        tub = yield Tub()
        tub.startService()
        yield  tub.getReference(uri).addCallbacks(self.__core_connect_success,
                                                  self.__core_connect_fail)

    def __core_connect_success(self, remote):
        log.debug("Connected to core")
        self.parent.connected_to_core(remote)
        self.hide()
        self.window.destroy()

    def __core_connect_fail(self, fail):
        log.debug("Failed to connect to core: %s", fail)

    def close_button_clicked_cb(self, widget):
        print 'close'
        self.hide()


    def start_service_button_clicked_cb(self, widget):
        log.debug("Starting local daemon")
        from afm.app import Application
        self.conn_status_task.stop()
        self.daemon_running = Application(self.parent.opts)
        self.daemon_running.start_services()
        self.conn_status_task.start(self.connection_update_interval,
                                          now=True)
        eventmanager.emit(DaemonStarted())

    def conn_treeview_selection_changed(self, selection):
        model, self.selected_connection_iter = selection.get_selected()
        log.debug("%s %s", model, self.selected_connection_iter)
        if self.selected_connection_iter:
            conn_status = model.get(self.selected_connection_iter, CON_STATUS)[0]
            log.debug("DR: %s", self.daemon_running)
            if self.daemon_running is None:
                if conn_status == ST_OFFLINE:
                    self.start_service_button.set_property('sensitive', True)
                else:
                    self.start_service_button.set_property('sensitive', False)

            if conn_status == ST_ONLINE:
                self.connect_button.set_property('sensitive', True)
            elif conn_status in (ST_OFFLINE, ST_CONNECTED):
                self.connect_button.set_property('sensitive', False)

            self.edit_connection_button.set_property('sensitive', True)
            self.delete_connection_button.set_property('sensitive', True)
        else:
            self.edit_connection_button.set_property('sensitive', False)
            self.delete_connection_button.set_property('sensitive', False)
            self.start_service_button.set_property('sensitive', False)
            self.connect_button.set_property('sensitive', False)

    def prepare_connections(self):
        self.conn_treeview = self.gladeTree.get_widget('connections_treeview')
        self._conn_create_model()
        self.conn_treeview.set_model(self.conn_model)
        self._conn_model_populate()
        self._conn_create_columns()
        self.conn_status_task.start(self.connection_update_interval, now=True)

    def _conn_create_model(self):
        self.conn_model = gtk.ListStore(gobject.TYPE_INT,        # Status
                                        gobject.TYPE_STRING,     # Name
                                        gobject.TYPE_STRING,     # URI
                                        gobject.TYPE_STRING,     # Version
                                        gobject.TYPE_STRING)     # Core URI


    def _conn_model_populate(self):
        for conn in self.parent.config.ui.servers.itervalues():
            self.conn_model.set(self.conn_model.append(),
                                CON_STATUS, ST_OFFLINE,
                                CON_NAME, conn.name,
                                CON_URI, conn.uri,
                                CON_VERSION, '',
                                CON_CORE_URI, '')

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

        # URI
        renderer = gtk.CellRendererText()
        renderer.set_data("column", CON_URI)
        column = gtk.TreeViewColumn('Url', renderer,
                                    text=CON_URI,
                                    editable=False)
        column.set_expand(True)
        self.conn_treeview.append_column(column)

        # Version
        renderer = gtk.CellRendererText()
        renderer.set_data("column", CON_VERSION)
        column = gtk.TreeViewColumn('Version', renderer,
                                    text=CON_VERSION,
                                    editable=False)
        self.conn_treeview.append_column(column)

    def _conn_status_cell_render(self, column, cell, model, row, data):
        status = model[row][data]
        pixbuf = None
        if status in range(3):
            pixbuf = self.conn_status_pixbuff[status]
        cell.set_property("pixbuf", pixbuf)

    def __update_core_version(self, remote_version, entry):
        log.debug("Got core version for URI %s: %s", entry[CON_URI],
                  remote_version)
        entry[CON_VERSION] = remote_version

    def __update_core_uri(self, core_uri, entry):
        log.debug("Got remote core URI for %s: %s", entry[CON_URI], core_uri)
        entry[CON_CORE_URI] = core_uri
        entry[CON_STATUS] = ST_ONLINE

    @defer.inlineCallbacks
    def __got_remote_reference(self, remote, entry):
        log.debug("Got remote tub reference for URI %s", entry[CON_URI])
        d = remote.callRemote('version')
        d.addCallback(self.__update_core_version, entry)
        d.addErrback(self.__remote_tub_failure, entry)
        yield d
        d = remote.callRemote('uri')
        d.addCallback(self.__update_core_uri, entry)
        d.addErrback(self.__remote_tub_failure, entry)
        yield d

    def __remote_tub_failure(self, fail, entry):
        log.debug("Failed to process remote call for URI %s: %s",
                  entry[CON_URI], fail)

    @defer.inlineCallbacks
    def _conn_update_details(self):
        for entry in self.conn_model:
            uri = entry[CON_URI]
            log.debug("Server connection Attempt: %s", uri)
            tub = Tub()
            tub.startService()
            d = tub.getReference(uri)
            d.addCallback(self.__got_remote_reference, entry)
            d.addErrback(self.__remote_tub_failure, entry)
            yield d

    def show(self, widget=None):
        self.conn_status_task.start(self.connection_update_interval, now=True)
        self.window.show_all()

    def hide(self, widget=None):
        self.conn_status_task.stop()
        self.window.hide_all()

    def toggle(self, widget=None):
        if self.window.get_property("visible"):
            self.hide()
        else:
            self.show()
