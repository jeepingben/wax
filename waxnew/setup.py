# -*- coding: utf-8 -*-

# Wax Chooser -- A utility for finding the ski wax best for the given conditions
#
# Copyright (C) 2010 Benjamin Deering <waxChooserMaintainer@swissmail.org>
# http://jeepingben.homelinux.net/wax/
#
# This file is part of Wax-chooser.
#
# Wax-chooser is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Wax-chooser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import glob
from waxChooser.const import APP_VERSION
from distutils.core import setup

def main():
    image_files = glob.glob("data/images/*.png")
    setup(name         = 'waxChooser',
          version      = APP_VERSION,
          description  = 'A utility for finding the appropriate ski wax',
          author       = 'Benjamin Deering',
          author_email = 'waxChooserMaintainer@swissmail.org',
          url          = 'http://jeepingben.homelinux.net/wax/',
          classifiers  = [
            'Development Status :: 5 - Production/Stable',
            'Environment :: X11 Applications',
            'Intended Audience :: End Users/Phone UI',
            'License :: GNU General Public License (GPL)',
            'Operating System :: POSIX',
            'Programming Language :: Python',
            'Topic :: Desktop Environment',
            ],
          packages     = ['waxChooser'],
          scripts      = ['waxChooser/waxChooser'],
          data_files   = [
            ('share/applications', ['data/wax.desktop']),
            ('share/pixmaps', ['data/waxChooser.png']),
            ('share/waxChooser', ['README', 'data/waxdb.db']),
	    ('share/waxChooser/images', image_files )
            ]
          )

if __name__ == '__main__':
    main()
