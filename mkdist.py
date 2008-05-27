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

import commands
import gzip
import os
import re
import sys
import tarfile
import time
import StringIO

version_tag = re.compile("^v\d+(\.\d+)*$")

def tag_parse(t):
    return [int(ti) for ti in t[1:].split(".")]

def tag_pad(s, l):
    return s + [0] * (l - len(s))

def tag_sort(a, b):
    a = tag_parse(a)
    b = tag_parse(b)

    a = tag_pad(a, len(b))
    b = tag_pad(b, len(a))

    return cmp(a, b)

def highest_version():
    tags = os.popen("git tag").readlines()
    tags = [t.strip() for t in tags if version_tag.match(t)]
    tags.sort(cmp=tag_sort)
    return tags[-1]

def main(args):
    if len(args) == 1:
        version = args[0]
    elif len(args) > 1:
        raise SystemExit, "Usage: %s [version]" % sys.argv[0]
    else:
        status, gitversion = commands.getstatusoutput("git-describe --tags")
        version = highest_version()
        if status != 0 or version != gitversion:
            raise SystemExit, """\
Highest version %r doesn't match description %r.
Specify version number explicitly if this is what you want""" % (
                    version, gitversion)

    version = version.lstrip("v")

    DIRNAME = "%(p)s-%(v)s" % {'p': 'mailpie', 'v': version}
    TARNAME = DIRNAME + '.tar.gz'

    verstream = StringIO.StringIO("%s\n" % version)
    verinfo = tarfile.TarInfo(DIRNAME + "/VERSION")
    verinfo.mode = 0660
    verinfo.size = len(verstream.getvalue())
    verinfo.mtime = time.time()

    tardata = os.popen("git-archive --prefix=%(p)s/ v%(v)s"
                            % {'p': DIRNAME, 'v': version}).read()
    tarstream = StringIO.StringIO(tardata)

    tar = tarfile.TarFile(mode="a", fileobj=tarstream)
    tar.addfile(verinfo, verstream)
    tar.close()

    out = gzip.open("../" + TARNAME, "wb")
    out.write(tarstream.getvalue())
    out.close()
    os.system("ls -l ../%s" % TARNAME)

if __name__ == '__main__':
    main(sys.argv[1:])
