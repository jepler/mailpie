import subprocess

def getoutput(cmdline):
    p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    p.stdin.close()
    return p.stdout.read()

def parsedate(s):
    return int(getoutput(["date", "-d%s" % s, "+%s"]))
