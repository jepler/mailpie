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

import email.Message
import email.Parser
import errno
import os
import string
import subprocess
import sys
import tempfile
import time
import rfc822
import mailpie.log
import mailpie.threaddb
import binascii

swishconfig_template = """
DefaultContents XML*
IndexFile %s
MetaNames header subject from to cc bcc list-id date
PropertyNamesDate date
MaxWordLimit 14
"""

parser = email.Parser.Parser()

def _get_index_files(base):
    return [base + ".index", base + ".index.recent"]

def get_index_files(base, all=False):
    return [path for path in _get_index_files(base) if all or os.path.exists(path)]

def index_exists(name):
    return os.path.exists(name)

def rename_index(old, new):
    print "rename_index", old, new
    os.rename(old, new)
    os.rename(old + ".prop", new + ".prop")

def unlink_index(name):
    os.unlink(name)
    os.unlink(name + ".prop")

def merge_index(target, additional):
    exists = os.path.exists(target)
    print "merge_index", target, additional, exists
    if not exists and len(additional) == 1:
        rename_index(additional[0], target)
        return

    merge = target + ".merge"
    swish_args = ['mailpie-flog', 'swish-e', '-M']
    if exists: swish_args += [target]
    swish_args += additional + [merge]
    os.spawnvp(os.P_WAIT, swish_args[0], swish_args)
    rename_index(merge, target)
    for index in additional: unlink_index(index)

class LockError(RuntimeError): pass

class Lock:
    def __init__(self, path, delay=.1, max_delay=3600):
        self.path = None
        while 1:
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                break
            except os.error, detail:
                if detail.errno != errno.EEXIST: raise
            if delay > max_delay: raise LockError, "Did not lock after %f seconds" % max_delay
            time.sleep(delay)
            delay = delay * 2
        self.path = path
        os.close(fd)

    def __del__(self):
        if self.path is not None:
            os.unlink(self.path)
            self.path = None

def write_one(path, mtime, data, dest=sys.stdout):
    dest.write("Path-name: %s\nLast-Mtime: %d\nContent-Length: %d\n\n" %(path, int(mtime), len(data)))
    dest.write(data)

null = string.maketrans("", "")
remove = "".join(chr(c) for c in range(32))
hremove = "".join(c for c in (chr(c) for c in range(256)) if not c in string.lowercase + string.uppercase + string.digits + "-")


def escape(s):
    s = s.translate(null, remove)
    s = s.replace("&", "&amp;");
    s = s.replace("<", "&lt;");
    s = s.replace(">", "&gt;");
    return s

def recode(payload, encoding):
    payload = payload.replace("", "")
    if isinstance(payload, unicode):
        return payload.encode("utf-8")
    encoding = encoding or "ascii"
    encoding = encoding.replace(" ", "")
    try:
        payload = payload.decode(encoding)
    except (UnicodeDecodeError, LookupError, binascii.Error):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = payload.decode("latin-1")
    return payload.encode("utf-8")
 
def recode_header(s):
    if isinstance(s, basestring):
        try:
            s = s.decode("utf-8")
        except UnicodeDecodeError:
            s = s.decode("latin-1")
    return s.encode("utf-8")

def get_payload(m):
    payload = m.get_payload()
    encoding = m.get_content_charset()
    if payload is None:
        mailpie.log.log("Payload is None in %s [%s]", m, repr(m._payload)[:20])
        return ''
    if isinstance(payload, basestring):
        if m.get_content_maintype() not in ("text", None): return ""
        payload = m.get_payload(decode=True) or payload
        payload = recode(payload, encoding)
        return escape(payload)
    result = []
    for p in payload:
        if not isinstance(p, email.Message.Message):
            mailpie.log.log("Unexpected payload item %s", p.__class__.__name__)
            continue
        result.append("<attachment>")
        result.append(get_payload(p))
        result.append("</attachment>")
    return "".join(result)

def parse_date(s):
    try:
        return str(int(rfc822.mktime_tz(rfc822.parsedate_tz(s))))
    except:
        mailpie.log.log("parse_date failed: %s", repr(s)[:50])
        return str(0)

date_fields = set(['date'])

def do_one(since, filename, key, thread_db, data=None, dest=sys.stdout):
    mtime = os.stat(filename).st_mtime
    if since:
        if mtime < since: return False
    if data:
        m = parser.parsestr(data)
    else:
        m = parser.parse(open(filename))
    result = ['<?xml version="1.0" encoding="UTF-8"?><message><header>']
    for h in m.keys():
        h = h.lower()
        for v in m.get_all(h):
            v = v.replace("\n", " ")
            v = v.replace("\t", " ")
            if h in date_fields: v = parse_date(v)
            v = recode_header(v)
            h = h.translate(null, hremove)
            result.append('<%s>%s</%s>\n' % (h, escape(v), h))
    result.append('</header><body>')
    result.append(get_payload(m))
    result.append('</body></message>')
    write_one(key, mtime, "".join(result), dest)

    thread_db.do_one(m, key)

    return True

class Incremental: pass

class Swish:
    def __init__(self, base, since=0, start=None):
        self.base = base
        if since is Incremental:
            lastfile = self.lastfile()
            if os.path.exists(lastfile):
                since = float(open(lastfile).read())
        full = (since == 0)
        self.since = since
        self.start = start
        self.lock = Lock(self.subfile("lock"))
        self.swishconfig = tempfile.NamedTemporaryFile()
        self.swishconfig.write(swishconfig_template % self.subfile("index"))
        self.swishconfig.flush()
        swishargs = ['mailpie-flog', 'swish-e', '-S', 'prog', '-i', 'stdin', '-c', self.swishconfig.name]
        if self.since: swishargs.extend(['-f', self.subfile("incremental")])
        self.swish = subprocess.Popen(swishargs, stdin=subprocess.PIPE)
        self.no_op = True
        self.thread_db = mailpie.threaddb.ThreadDB(self.base, full)

    def subfile(self, ext): return self.base + "." + ext
    def lastfile(self): return self.subfile("last")

    def close(self):
        self.thread_db.close()
        self.swish.stdin.close()
        result = self.swish.wait()
        if not self.no_op:
            if result != 0: raise RuntimeError, "swish-e exited with code %d" % result
            if self.since:
                merge_index(self.subfile("index.recent"), [self.subfile("incremental")])
        if self.start:
            open(self.lastfile(), "w").write(str(self.start))

    def merge(self):
        if index_exists(self.subfile("index.recent")):
            merge_index(self.subfile("index"), [self.subfile("index.recent")])

    def do_one(self, filename, key, data=None):
        if do_one(self.since, filename, key, self.thread_db, data, self.swish.stdin):
            self.no_op = False
