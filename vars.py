import os, sys
from atoi import atoi
from helpers import close_on_exec
import runid


# The absolute path that was os.getcwd() when we started.
STARTDIR = os.environ.get('REDO_STARTDIR', '')

# A user-friendly printable version of os.getcwd() (ie. the location of the
# currently running .do file) relative to STARTDIR.
# For example, ../foo/blah
# This is better to use than os.path.relpath, because your paths might include
# symlinks that make a/b/../c not equal to a/c.
PWD = os.environ.get('REDO_PWD', '')

# The path where .do files are searched
SOURCE_DIR = os.path.realpath(os.environ.get('REDO_SOURCE_DIR', '.'))

# The path where result of build is placed
TARGET_DIR = os.path.realpath(os.environ.get('REDO_TARGET_DIR', '.'))

# The path to the target currently being built, relative to PWD.
TARGET = os.environ.get('REDO_TARGET', '')

# The depth of redo recursion, in the form of a string of space characters.
# The deeper we go, the more space characters we append.
DEPTH = os.environ.get('REDO_DEPTH', '')

# The value of the --overwrite flag.
OVERWRITE = os.environ.get('REDO_OVERWRITE', '') and 1 or 0

# The value of the -d flag.
DEBUG = atoi(os.environ.get('REDO_DEBUG', ''))

# The value of the --debug-pids flag.
DEBUG_PIDS = os.environ.get('REDO_DEBUG_PIDS', '') and 1 or 0

# The value of the --debug-locks flag.
DEBUG_LOCKS = os.environ.get('REDO_DEBUG_LOCKS', '') and 1 or 0

# The value of the --old-args flag.
OLD_ARGS = os.environ.get('REDO_OLD_ARGS', '') and 1 or 0

# The value of the --old-stdout flag.
OLD_STDOUT = os.environ.get('REDO_OLD_STDOUT', '') and 1 or 0

# The value of the --warn-stdout flag.
WARN_STDOUT = os.environ.get('REDO_WARN_STDOUT', '') and 1 or 0

# The value of the --only-log flag.
ONLY_LOG = os.environ.get('REDO_ONLY_LOG', '') and 1 or 0

# The value of the -v flag.
VERBOSE = os.environ.get('REDO_VERBOSE', '') and 1 or 0

# The value of the -x flag.
XTRACE = os.environ.get('REDO_XTRACE', '') and 1 or 0

# The value of the -k flag.
KEEP_GOING = os.environ.get('REDO_KEEP_GOING', '') and 1 or 0

# The value of the --shuffle flag.
SHUFFLE = os.environ.get('REDO_SHUFFLE', '') and 1 or 0

# The value of the --color flag, or an auto detected value.
_color = sys.stderr.isatty() and (os.environ.get('TERM') or 'dumb') != 'dumb'
COLOR = atoi(os.environ.get('REDO_COLOR', '1' if _color else '0'))
if 'REDO_COLOR' not in os.environ: os.environ['REDO_COLOR'] = str(COLOR)

# The REDO_LOGFD file descriptor
LOGFD = atoi(os.environ.get('REDO_LOGFD', ''), None)

# The REDO_LOGFD file descriptor
LOG = atoi(os.environ.get('REDO_LOG', '0'), 0)

# The id of the current redo execution; an int(time.time()) value.
RUNID_FILE = os.environ.get('REDO_RUNID_FILE')


def init():
    if not os.environ.get('REDO'):
        import sys
        sys.stderr.write('%s: error: must be run from inside a .do\n'
                         % sys.argv[0])
        sys.exit(100)
    global RUNID
    RUNID = runid.read(os.path.join(STARTDIR, RUNID_FILE))

def reinit():
    reload(sys.modules[__name__])
    init()

def cleanup_on_exec():
    if LOGFD:
        close_on_exec(LOGFD, True)

    close_on_exec(0, True)
    close_on_exec(1, True)
    close_on_exec(2, True)
    STDIO = os.environ.get('REDO_STDIO')
    if STDIO:
        try:
            a, b, c = [int(x) for x in STDIO.split(',')]
            os.dup2(a, 0)
            os.dup2(b, 1)
            os.dup2(c, 2)
            close_on_exec(a, True)
            close_on_exec(b, True)
            close_on_exec(c, True)
        except: pass

    for env in ['REDO', 'REDO_STARTDIR', 'REDO_PWD', 'REDO_TARGET',
        'REDO_DEPTH', 'REDO_OVERWRITE', 'REDO_DEBUG', 'REDO_DEBUG_PIDS',
        'REDO_DEBUG_LOCKS', 'REDO_OLD_ARGS', 'REDO_OLD_STDOUT',
        'REDO_WARN_STDOUT', 'REDO_ONLY_LOG', 'REDO_VERBOSE', 'REDO_XTRACE',
        'REDO_KEEP_GOING', 'REDO_SHUFFLE', 'REDO_LOGFD', 'REDO_RUNID_FILE',
        'REDO_STDIO']:
        try:    del os.environ[env]
        except: pass

