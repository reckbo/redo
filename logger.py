import sys, os
import vars, state
from helpers import close_on_exec, unlink
from log import log, err, warn, LOGFILE, _cmd_encode


def open_log(t=None, truncate=False):
    if not vars.LOG: return None
    if not t:
        t = state.File(vars.TARGET)
    f = t.tmpfilename('log')
    flags = os.O_WRONLY|os.O_APPEND|os.O_EXCL
    if truncate:
        unlink(f)
        flags = flags|os.O_CREAT
    fd = os.open(f, flags, 0666)
    return fd

try:
    LOGCMD  = open_log()
    LOCKCMD = state.Lock(f=LOGCMD)
except:
    LOGCMD  = None
    LOCKCMD = None

class Logger:
    def __init__(self, logfd, stdoutfd):
        self.stdoutfd = stdoutfd
        self.logfd    = logfd
        if vars.LOG:
            self.fd_std_in, self.fd_std_out = os.pipe()
            self.fd_err_in, self.fd_err_out = os.pipe()
            self.fd_log_in, self.fd_log_out = os.pipe()

    def fork(self):
        if not vars.LOG:
            if vars.OLD_STDOUT or vars.WARN_STDOUT:
                os.dup2(self.stdoutfd, 1)
            return
        pid = os.fork()
        if pid == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_log_out)
            os.close(self.fd_err_in)
            os.close(self.fd_log_in)
            sysout = sys.stdout
            if vars.OLD_STDOUT: sysout = None
            self._main(os.fdopen(self.fd_std_in), "std", sysout, self.stdoutfd)
            os._exit(0)
        pid2 = os.fork()
        if pid2 == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_log_out)
            os.close(self.fd_std_in)
            os.close(self.fd_log_in)
            os.close(self.stdoutfd)
            self._main(os.fdopen(self.fd_err_in), "err", sys.stderr)
            os._exit(0)
        pid3 = os.fork()
        if pid3 == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_log_out)
            os.close(self.fd_std_in)
            os.close(self.fd_err_in)
            os.close(self.stdoutfd)
            self._main(os.fdopen(self.fd_log_in), "log", LOGFILE)
            os._exit(0)
        os.dup2(self.fd_std_out, 1)
        os.dup2(self.fd_err_out, 2)
        os.close(self.fd_std_out)
        os.close(self.fd_err_out)
        os.close(self.fd_std_in)
        os.close(self.fd_err_in)
        os.close(self.fd_log_in)
        close_on_exec(self.fd_log_out, False)
        close_on_exec(1, False)
        close_on_exec(2, False)

        if vars.LOGFD: os.close(vars.LOGFD)
        os.environ["REDO_LOGFD"] = str(self.fd_log_out)
        vars.reinit()

        os.close(self.logfd)

    def _main(self, f, stamp, sysout=None, stdoutfd=None):
        try:
            from setproctitle import setproctitle
        except ImportError:
            pass
        else:
            setproctitle("redo %s logger" % stamp)
        try:
            lck = state.Lock(f=self.logfd)
            l = f.readline(1024)
            while len(l):
                with lck.write():
                    os.write(self.logfd, _cmd_encode(stamp, l))
                    os.fsync(self.logfd)
                if not vars.ONLY_LOG and sysout:
                    os.write(sysout.fileno(), l)
                    try: os.fsync(sysout.fileno())
                    except: pass
                if stdoutfd:
                    os.write(stdoutfd, l)
                    os.fsync(stdoutfd)
                l = f.readline(1024)
        except KeyboardInterrupt:
            os._exit(200)

class LogPrinter:
    def __init__(self, target, recursive):
        self.target    = target
        self.recursive = recursive
        self.logfile   = target.tmpfilename('log')
        self.flushcmd  = None
        self.doing     = None

    def _flush(self, buf):
        if self.flushcmd == "redo" and self.recursive:
            f = buf[:-1]
            olddepth = vars.DEPTH
            vars.DEPTH = vars.DEPTH + '  '
            try:
                main([os.path.join(self.target.dirname(), f)])
            finally:
                vars.DEPTH = olddepth
            self.doing = buf
        elif self.flushcmd == "redo_done" and self.doing == buf:
            self.doing = None
        elif self.flushcmd == "std" and self.doing == None:
            sys.stdout.write(buf)
            sys.stdout.flush()
        elif self.flushcmd == "err" and self.doing == None:
            sys.stderr.write(buf)
            sys.stderr.flush()
        elif self.flushcmd == "log" and not self.recursive:
            LOGFILE.write(buf)
            LOGFILE.flush()
        elif self.flushcmd == "redo_err" and self.recursive:
            err("  " + buf)
        elif self.flushcmd == "redo_warn" and self.recursive:
            warn("  " + buf)

    def printer(self):
        command = False
        cmdbuf = ""
        argbuf = ""
        with open(self.logfile, "r") as f:
            for line in f:
                for c in line:
                    if command:
                        command = (c != "\0")
                        if command:
                            cmdbuf += c
                        elif cmdbuf == "z":
                            argbuf += "\0"
                        else:
                            self._flush(argbuf)
                            self.flushcmd = cmdbuf
                            argbuf = ""
                    else:
                        if c == "\0":
                            cmdbuf = ""
                            command = True
                        else:
                            argbuf += c
        self._flush(argbuf)


def print_log(t, recursive=False):
    LogPrinter(t, recursive).printer()


def main(targets, toplevel=False):
    for t in targets:
        f = state.File(srcname=t)
        l = f.tmpfilename('log')
        try:
            # Try to get lock to tell if the process is still running. If we
            # don't get it, that's not important, the log file is append only
            f.dolock().trylock(state.LOCK_SH)

            if not os.path.exists(l):
                err('%s: no log\n', f.printable_name())
            else:
                log('%s\n', f.printable_name())
                print_log(f, recursive=True)
            if not f.dolock().owned:
                log('%s (still running)\n', f.printable_name())
            elif f.exitcode == 0:
                log('%s (done)\n', f.printable_name())
            elif toplevel and f.exitcode != None:
                err('%s: exit code %d\n', f.printable_name(), f.exitcode)
        finally:
            if f.dolock().owned: f.dolock().unlock()
