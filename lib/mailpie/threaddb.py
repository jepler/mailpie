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
import bsddb

class ThreadDB:
    def __init__(self, base):
        self.db = bsddb.hashopen(base + ".thread.db")
        self._cache = {}

    def close(self):
        for k, v in self._cache.items():
            self.db[k] = " ".join(v)
        self.db.close()

    def threads(self, message):
        for h in message.get_all("in-reply-to", []):
            for word in h.split(): yield word
        for h in message.get_all("references", []):
            for word in h.split(): yield word

    def do_one(self, message, hash):
        msgid = message.get("message-id")
        if msgid is None: return
        self.db["h:" + hash] = msgid
        self.db['m:' + msgid] = hash
        threads = set(self.threads(message))
        self.cache("t:" + msgid).update(threads)
        for t in threads: self.cache("t:" + t).add(msgid)

    def cache(self, k):
        if not k in self._cache:
            if len(self._cache) > 1000:
                while len(self._cache) > 500:
                    k, v = self._cache.popitem()
                    self.db[k] = " ".join(v)
            self._cache[k] = set(self.db.get(k, "").split())
        return self._cache[k]
