#!/usr/bin/python
# vim: set fileencoding=utf-8 : sts=4 : et : sw=4
#    This is a component of mailpie, a full-text search for email
#
#    Copyright © 2008 Jeff Epler <jepler@unpythonic.net>
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from distutils.core import setup
import os

def require_program(s):
    for el in os.environ['PATH'].split(os.pathsep):
        j = os.path.join(el, s)
        if os.access(j, os.F_OK | os.X_OK):
            return True
    print "Warning: The required external program %r is not available." % s
    print "The software will probably not work without it."
    return False

for p in ["swish-e"]: require_program(p)

setup(name="mailpie", version="0.1",
    author="Jeff Epler", author_email = "jepler@unpythonic.net",
    packages=['mailpie'], package_dir={'mailpie': 'lib/mailpie'},
    scripts=['scripts/mailpie-add', 'scripts/mailpie-index', 'scripts/mailpie-search'],
    url="http://emergent.unpy.net/software/aethertool/",
    license="GPL",
)
# vim:sw=4:sts=4:et

