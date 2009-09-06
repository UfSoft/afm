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


class ConnectionsManager(GladeWidget):
    gladefile = 'ConnectionsManager.glade'

    def prepare_widget(self):
        pass

    def on_new_connection_button_activate(self):
        connection_details = ConnectionDetails(self)
        connection_details.show()

    def on_delete_connection_button_activate(self):
        pass

    def on_connect_button_activate(self):
        pass

    def on_exit_button_activate(self):
        pass
