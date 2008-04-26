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
import rfc822

swishconfig_template = """
DefaultContents XML*
IndexFile %s
MetaNames subject from to cc bcc list-id message-id date
PropertyNames in-reply-to references
PropertyNamesDate date
MaxWordLimit 999
"""

parser = email.Parser.Parser()

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
    except (UnicodeDecodeError, LookupError):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = payload.decode("latin-1")
    return payload.encode("utf-8")
 
def get_payload(m):
    payload = m.get_payload()
    encoding = m.get_content_charset()
    if payload is None:
        print >>sys.stderr, "Payload is None in", m, repr(m._payload)[:20]
        return ''
    if isinstance(payload, basestring):
        if m.get_content_maintype() not in ("text", None): return ""
        payload = m.get_payload(decode=True) or payload
        payload = recode(payload, encoding)
        return escape(payload)
    result = []
    for p in payload:
        if not isinstance(p, email.Message.Message):
            print >>sys.stderr, "Unexpected payload item", p.__class__.__name__
            continue
        result.append("<attachment>")
        result.append(get_payload(p))
        result.append("</attachment>")
    return "".join(result)

def parse_date(s):
    try:
        return str(int(rfc822.mktime_tz(rfc822.parsedate_tz(s))))
    except:
        print >>sys.stderr, "parse_date failed:", repr(s)[:50]
        return str(0)

date_fields = set(['date'])

def do_one(since, filename, key, data=None, dest=sys.stdout):
    mtime = os.stat(filename).st_mtime
    if since:
        if mtime < since: return
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
            result.append('<%s>%s</%s>\n' % (h, escape(v), h))
    result.append('</header><body>')
    result.append(get_payload(m))
    result.append('</body></message>')
    write_one(key, mtime, "".join(result), dest)

class Incremental: pass

class Swish:
    def __init__(self, base, since=0, start=None):
        self.base = base
        if since is Incremental:
            lastfile = self.lastfile()
            if os.path.exists(lastfile):
                since = float(open(lastfile).read())
        self.since = since
        self.start = start
        self.lock = Lock(self.subfile("lock"))
        self.swishconfig = tempfile.NamedTemporaryFile()
        self.swishconfig.write(swishconfig_template % self.subfile("index"))
        self.swishconfig.flush()
        swishargs = ['swish-e', '-S', 'prog', '-i', 'stdin', '-c', self.swishconfig.name]
        if not os.path.exists(self.subfile("index")): self.since=0
        if self.since: swishargs.extend(['-f', self.subfile("incremental")])
        self.swish = subprocess.Popen(swishargs, stdin=subprocess.PIPE)

    def subfile(self, ext): return self.base + "." + ext
    def lastfile(self): return self.subfile("last")

    def close(self):
        self.swish.stdin.close()
        result = self.swish.wait()
        if result != 0: raise RuntimeError, "swish-e exited with code %d" % result
        if self.since:
            os.spawnvp(os.P_WAIT, 'swish-e', ['swish-e', '-M', self.subfile("index"), self.subfile("incremental"), self.subfile("merge")])
            os.rename(self.subfile("merge"), self.subfile("index"))
            os.rename(self.subfile("merge.prop"), self.subfile("index.prop"))
            os.unlink(self.subfile("incremental"))
            os.unlink(self.subfile("incremental.prop"))
        if self.start:
            open(self.lastfile(), "w").write(str(self.start))

    def do_one(self, filename, key, data=None):
        do_one(self.since, filename, key, data, self.swish.stdin)
