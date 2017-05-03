# mailpie - e-mail full text search

## PURPOSE

mailpie is a suite of programs for commandline full-text search of large
e-mail archives.  Keep your inbox uncluttered while retaining the
ability to quickly find an old message that becomes relevant again.

In fact, mailpie performs searches much more quickly than many MUAs'
built in search facilities because it uses a time-tested full text
indexer (swish-e).


## DEVELOPMENT STATUS

Mature.  Mailpie is unlikely to receive future updates from @jepler.
Instead, I recommend you consider maintained alternatives like [notmuch](https://notmuchmail.org/).
I am open to a new maintainer taking over mailpie.


## REQUIREMENTS

 - python with bsddb support (tested with python 2.7.3)
 - swish-e (tested with swish-e 2.4.7)

mailpie is developed on Debian GNU/kFreeBSD systems.


## INSTALLATION

Site-wide installation:

    $ sudo python setup.py install

Personal installation:

    $ python setup.py install --home=$HOME

Make sure that $HOME/lib/python is on PYTHONPATH

See distutils documentation for more installation options.

You can also add variables to your bourne-like shell's environment so
that you can invoke the commands in scripts/ using the modules from lib/
(e.g., to test without installing):

    $ . environ.sh    

## USAGE

To add a mailbox full of messages to the mailpie storage:

    mailpie-add example.mbox

After adding messages with mailpie-add, the original mbox file is not
needed to perform searches.

To search for messages:

    mailpie-search --after="April 1" from=jepler mutt

This will find messages dated after April 1 where the From: line matches
'jepler' and the header or body matches 'mutt'.

Available search tags are:

    header subject from to cc bcc list-id

Without a tag, the message headers and body are all searched.

To rebuild the index from scratch (e.g., in case of an aborted
mailpie-add):

    mailpie-index

For more information on commandline options, see mailpie-xxx --help.


## TIPS

Because swish-e can take a long time to merge two index files together,
mailpie uses a two-level index system.  mailpie-add puts new messages in
"index.recent".  When this index grows large enough that the merge operation
becomes slow, run "mailpie-index -im" to merge "index.recent" into the main
index (this may take quite a long time).  After that, mailpie-add will be fast
again.


## PRINCIPLE

mailpie-add splits mailboxes into individual messages, which are stored
in separate files according to their sha1 hash.

When indexing, mailpie-add and mailpie-index convert each message into
an xml document with markup that indicates headers that should be
indexed specially (e.g., with the `<from>...</from>` tag).  These xml
documents are then handed off to swish-e to index.

When searching, mailpie-search involkes swish-e to find the messages
that match the given search terms.  It concatentates each message into
an mbox and then optionally invokes a mailreader.  Optionally,
mailpie-search follows in-reply-to and references to find other messages
in the same thread as matching messages.


## EFFICIENCY

When adding thousands of messages, the average rate on a 1.8GHz machine
is 60/second.

When searching tens of thousands of messages, the time is well under 1
second for 100 results when the swish indexes are in memory.


## NON-FEATURES

The following features are outside the scope of mailpie and are unlikely
to be added:

 * A Graphical User Interface
 * Support for mailbox formats other than 'mbox'


## RELEASE HISTORY

### v0.4.6

 * Fix several ways to get the error 'File exists' in maildir mode
 * Port to Debian GNU/kFreeBSD 7

### v0.4.5

 * Fix build with newer git versions
 * Invoke mutt without its normal list of mailboxes (can speed startup)
 * Optionally include links to Gmake based on message IDs
 * Fix parsing of before= search term
 * Add maildir support (faster copymail)
 * Try harder to recognize valid message IDs
 * Start with fresh ThreadDB when doing full index
 * Avoid crash on certain misencoded messages
 * Fix determination of screen size
 * Get syntax highlighting for this file
 * Make thread chasing message more useful
 * Add license notices
 * Fix some errors seen when freshly indexing all my mail
 * Only autorun mailer when stdout is a terminal
 * Fix quoting of arguments to swish
 * Debian packaging

### v0.4.1

 * Don't ship copies of images included in asciidoc

### v0.4

 * mailpie-search: Improved error reporting when swish is unhappy with search
   terms
 * mailpie-search: Improved progress reporting
 * mailpie-search: Mailreader may come from environment variable
 * mailpie-add, mailpie-index: clean up progress messages from swish when
   output is going to email or other non-terminal destination
 * mailpie-admin: new tool to get database statistics or remove messages
   (e.g., spam that got in the index)
 * use a separate threading database.  When upgrading, run mailpie-index
   -f to create this index
 * Documentation in the doc/ directory.  builds using asciidoc or readable
   as-is

### v0.3

 * mailpie-add: fix typo that caused it to error at the end

### v0.2

 * mailpie-add: improve speed of by introducing two levels of index
 * mailpie-add: fix time report when there are zero tens-of-seconds
 * mailpie-search: -l, --after=, --before=, and --limit=  to take arguments
 * mailpie-search: improve -N flag to configure mailreader
 * mailpie-index: add --merge action
 * all: improve usage messages
 * all: improve progress reporting

### v0.1
 * Initial release

## COPYRIGHT

Copyright © 2008-2013 Jeff Epler <jepler@unpythonic.net>
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
                                                                          
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
                                                                          
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
