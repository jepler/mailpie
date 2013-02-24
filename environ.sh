#!/bin/bash
mailpie_home=$HOME/mailpie
PATH=$mailpie_home/scripts:$PATH
PYTHONPATH=$mailpie_home/lib${PYTHONPATH:+:}${PYTHONPATH}
export PATH PYTHONPATH
