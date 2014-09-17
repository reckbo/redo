def main_redo(redo_flavour, targets):
    import builder, state

    targets = state.fix_chdir(targets)
    return builder.main(targets)

def main_redo_log(redo_flavour, targets):
    import state, logger

    targets = state.fix_chdir(targets)
    return logger.main(targets, toplevel=True)

def main_redo_exec(redo_flavour, args):
    import sys, os
    import vars, jwack
    from log import log, err

    if len(args) == 0:
        return 0

    log("exec %s\n", " ".join(args))
    vars.cleanup_on_exec()
    jwack.cleanup_on_exec()

    try:
        os.execlp(args[0], *args)
    except OSError, e:
        err("exec %s: %s\n", e.filename or args[0], e.strerror)
        return 1

def main_redo_delegate(redo_flavour, targets):
    import builder, state, vars
    from log import debug2

    if vars.TARGET:
        f = state.File(name=vars.TARGET)
        debug2('TARGET: %r %r %r\n', vars.STARTDIR, vars.PWD, vars.TARGET)
    else:
        f = None
        debug2('%S: no target - not delegating.\n', redo_flavour)

    targets = state.fix_chdir(targets)
    return builder.main(targets, delegate=f)

def main_redo_ifchange(redo_flavour, targets):
    import ifchange, state, vars, builder
    from log import debug2

    if vars.TARGET:
        f = state.File(name=vars.TARGET)
        debug2('TARGET: %r %r %r\n', vars.STARTDIR, vars.PWD, vars.TARGET)
    else:
        f = None
        debug2('%s: no target - not adding depends.\n', redo_flavour)

    targets = state.fix_chdir(targets)
    return builder.main(targets, ifchange.should_build, f, re_do=False)

def main_redo_ifcreate(redo_flavour, targets):
    import os
    import vars, state
    from log import err

    targets = state.fix_chdir(targets)
    f = state.File(vars.TARGET)
    for t in targets:
        if os.path.exists(t):
            err('%s: error: %r already exists\n', redo_flavour, t)
            return 1
        else:
            f.add_dep(state.File(name=t))

def main_redo_always(redo_flavour, targets):
    import vars, state

    state.fix_chdir([])
    f = state.File(vars.TARGET)
    f.add_dep(state.File(name=state.ALWAYS))

def main_redo_stamp(redo_flavour, targets):
    import os
    import vars, state

    if len(targets) > 1:
        err('%s: no arguments expected.\n', redo_flavour)
        return 1

    if os.isatty(0):
        err('%s: you must provide the data to stamp on stdin\n', redo_flavour)
        return 1

    # hashlib is only available in python 2.5 or higher, but the 'sha' module
    # produces a DeprecationWarning in python 2.6 or higher.  We want to support
    # python 2.4 and above without any stupid warnings, so let's try using hashlib
    # first, and downgrade if it fails.
    try:
        import hashlib
    except ImportError:
        import sha
        sh = sha.sha()
    else:
        sh = hashlib.sha1()

    while 1:
        b = os.read(0, 4096)
        sh.update(b)
        if not b: break

    csum = sh.hexdigest()

    if not vars.TARGET:
        return 0

    state.fix_chdir([])
    f = state.File(vars.TARGET)
    f._add('%s .' % csum)

def main_redo_isuptodate(redo_flavour, targets):
    import vars, state, deps
    from log import err, log

    if 'all' in targets:
        targets.remove('all')
    if len(targets) != 1:
        err('%s: only one argument expected.\n', redo_flavour)
        return 1

    f = state.File(targets[0])
    if f.is_generated and f.exists() and not deps.isdirty(f, depth='', expect_stamp=f.stamp):
        log('%s is up to date.\n', f.name)
        return 0
    if not f.is_generated and f.exists():
        log('%s is a source file.\n', f.name)
        return 0
    log('%s is not an up to date file.\n', f.name)
    return 1

def main_redo_filestamp(redo_flavour, targets):
    import vars, state, deps
    from log import err, log
    import os

    if 'all' in targets:
        targets.remove('all')
    if len(targets) != 1:
        err('%s: only one argument expected.\n', redo_flavour)

    #f = state.File(targets[0])
    st = os.stat(targets[0])
    print state.Stamp(st = st).stamp
    return 0

def main_redo_ood(redo_flavour, targets):
    import vars, state, deps
    from log import err

    if 'all' in targets:
        targets.remove('all')
    if len(targets) != 0:
        err('%s: no arguments expected.\n', redo_flavour)
        return 1

    for f in state.files():
        if f.is_generated and f.exists():
            if deps.isdirty(f, depth='', expect_stamp=f.stamp):
                print f.name

def main_redo_sources(redo_flavour, targets):
    import state
    from log import err

    if 'all' in targets:
        targets.remove('all')
    if len(targets) != 0:
        err('%s: no arguments expected.\n', redo_flavour)
        return 1

    for f in state.files():
        if f.name.startswith('//'):
            continue  # special name, ignore
        if not f.is_generated and f.exists():
            print f.name

def main_redo_targets(redo_flavour, targets):
    import state
    from log import err

    if len(targets) != 0:
        err('%s: no arguments expected.\n', redo_flavour)
        return 1

    for f in state.files():
        if f.is_generated and f.exists():
            print f.name

def main_redo_dofile(redo_flavour, targets):
    import os.path
    import state, builder

    res = 0

    targets = state.fix_chdir(targets)
    for target in targets:
        f = state.File(name=target)
        dodir,dofile,basedir,basename,ext = builder._find_do_file(f)
        if dodir:
            print os.path.join(dodir, dofile)
        else:
            res = res + 1

    return res


mains = {
    'redo-filestamp':  main_redo_filestamp,
    'redo-isuptodate':  main_redo_isuptodate,
    'redo-sources':  main_redo_sources,
    'redo-targets':  main_redo_targets,
    'redo-ood':      main_redo_ood,
    'redo-stamp':    main_redo_stamp,
    'redo-always':   main_redo_always,
    'redo-ifcreate': main_redo_ifcreate,
    'redo-ifchange': main_redo_ifchange,
    'redo-delegate': main_redo_delegate,
    'redo-log':      main_redo_log,
    'redo-exec':     main_redo_exec,
    'redo-dofile':   main_redo_dofile,
    'redo':          main_redo}
