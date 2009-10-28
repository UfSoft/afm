# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging
from os import listdir
from os.path import join
from lxml import etree
from twisted.python.reflect import namedAny

log = logging.getLogger(__name__)

PARAM_TYPES = {
    None:    str,
    'str':   str,
    'int':   int,
    'bool':  lambda x: bool(int(x)),
    'float': float
}

DEFAULT_CONFIG = {
    'ui': {
        'show_splash': {}
    },
    'servers': [{
            'name':     'Localhost',
            'hostname': 'localhost',
            'port':     58848,
            'username': 'test',
            'password': 'test'
        }
    ]
}

class ConfigParam(object):
    def __init__(self, node):
        self.name = node.get('name').replace('-', '_')
        self.type = node.get('type')
        value = node.get('value')
        self.value = PARAM_TYPES[self.type](value)

class ConfigAttribute(object):

    def __init__(self, **kwargs):
        self.__dict__ = dict(**kwargs)
#        self.keys       = self.__dict__.keys
        self.values     = self.__dict__.values
        self.items      = self.__dict__.items
        self.iterkeys   = self.__dict__.iterkeys
        self.itervalues = self.__dict__.itervalues
        self.iteritems  = self.__dict__.iteritems
        self.__iter__   = self.__dict__.__iter__

    def __hasattr__(self, attr):
        return attr in self.__dict__

    def keys(self):
        return filter(lambda x: x not in ('keys', 'values', 'items',
                                          'iterkeys', 'itervalues',
                                          'iteritems', '__iter__'),
                                          self.__dict__.keys())

class Configuration(object):
    """Server configuration"""

    def __init__(self, configdir):
        self.configdir = configdir
        self.configfile = join(configdir, 'afm.xml')
        self.tree = etree.parse(self.configfile)
        self.root = self.tree.getroot()
        self.defaults = DEFAULT_CONFIG.copy()

    def load_core_config(self):
        log.debug("Loading Core Configuration")
        # Daemon configuration
        node = self.root.find('daemon')
        core = ConfigAttribute()
        for param_node in node.findall('param'):
            param = ConfigParam(param_node)
            log.debug("On param node %r with value %r", param.name, param.value)
            setattr(core, param.name, param.value)
        self.core = core
        self.core.__node__ = node

#        # Core Users
#        node = node.find('users')
#        users = {}
#        for user_node in node.findall('user'):
#            user_config = UserConfig(user_node)
#            log.debug('User %r can access the core', user_config.username)
#            users[user_config.username] = user_config
#        self.users = users
        self.load_sources_config()

    def load_sources_config(self):
        log.debug("Loading Sources Configuration")
        # Sources configuration
        sources = {}
        for filename in listdir(join(self.configdir, 'sources')):
            if filename.endswith('.xml'):
                log.debug("Found source filename %r", filename)
                config = SourceConfig(join(self.configdir, 'sources', filename))
                sources[config.name] = config
        self.sources = sources

    def load_ui_config(self):
        log.debug("Loading Connections Configuration")
        node = self.root.find('ui')
        ui = ConfigAttribute()
        for param_node in node.findall('param'):
            param = ConfigParam(param_node)
            log.debug("On param node %r with value %r", param.name, param.value)
            setattr(ui, param.name, param.value)
        self.ui = ui
        self.ui.__node__ = node
        self.load_server_connections_config()

    def load_server_connections_config(self):
        node = self.ui.__node__.find('servers')
        servers = {}
        for server_node in node.findall('server'):
            server = ServerConfig(server_node)
            print server
            servers[server.name] = server
        self.ui.servers = servers

    def save(self, output):
        # UI
        tree = etree.Element('afm-config')
        section = etree.Element('ui')
        for key in self.ui.keys():
            node = self.ui_node.xpath('param[@name="%s"]' % key)
            if node:
                node = node[0].attrib[key] = getattr(self.ui, key)
        tree.append(section)
        section = etree.Element('servers')
        for name, details in self.servers.iteritems():
            server = etree.Element('server', name=name)
            for name in ('name', 'hostname', 'port', 'username', 'password'):
                value = getattr(details, name)
                param = etree.Element(
                    'param',
                    name=name,
                    value=str(value),
                    type=type(value).__name__
                )
                server.append(param)
            section.append(server)
        tree.append(section)
        root = etree.ElementTree(element=tree)
        root.write(output, pretty_print=True, xml_declaration=True,
                   encoding='UTF-8')


class SourceConfig(object):

    def __init__(self, configfile):
        self.configfile = configfile
        self.tree = etree.parse(self.configfile)
        self.root = self.tree.getroot()
        self.name = self.root.get('name').encode('utf-8')
        self.uri = self.root.get('uri')
        self.load_params()
        log.debug("Loading Audio Source '%s' '%s'", self.name, self.uri)

    def load_params(self):
        params_node = self.root.find('params')
        for param_node in params_node.findall('param'):
            param = ConfigParam(param_node)
            setattr(self, param.name, param.value)

    def get_tests(self, source):
        tests = self.root.find('tests')
        for test in tests.findall('test'):
            yield load_test(source, test)
        raise StopIteration

    def __repr__(self):
        return '<SourceConfig name="%(name)s" uri="%(uri)s">' % self.__dict__

class ServerConfig(object):
    def __init__(self, tree_node):
        self.root = tree_node
        self.name = tree_node.get('name').encode('utf-8')
        self.uri = tree_node.get('uri').encode('utf-8')
        log.debug("Loading server connection '%s'", self.name)

def load_test(source, xmlconfig):
    params = {}
    module_name = xmlconfig.get('module')
    class_name = xmlconfig.get('class')
    params_node = xmlconfig.find('params')
    for param_node in params_node.findall('param'):
        param = ConfigParam(param_node)
        params[param.name] = param.value

#    module = __import__(module_name, globals(), locals(), [''])
#    klass = getattr(module, class_name)
#    return klass(source, **params)
    return namedAny('.'.join([module_name, class_name]))(source, **params)
