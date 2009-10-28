#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

from setuptools import setup
import afm

setup(name=afm.__package__,
      version=afm.__version__,
      author=afm.__author__,
      author_email=afm.__email__,
      url=afm.__url__,
      download_url='http://python.org/pypi/%s' % afm.__package__,
      description=afm.__summary__,
      long_description=afm.__description__,
      license=afm.__license__,
      platforms="OS Independent - Anywhere Twisted and GStremaer is known to run.",
      keywords = "Twisted Gstreamer",
      packages=['afm'],
      install_requires = ['foolscap'],
#      package_data={
#          'sshg': ['upgrades/*.cfg']
#      },
      entry_points = """
      [console_scripts]
      afm-daemon = afm.service:daemon
      afm-client = afm.service:client

      [distutils.commands]
      compile = babel.messages.frontend:compile_catalog
      extract = babel.messages.frontend:extract_messages
         init = babel.messages.frontend:init_catalog
       update = babel.messages.frontend:update_catalog
      """,
      classifiers=[
          'Development Status :: 5 - Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Utilities',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
      ]
)
