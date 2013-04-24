import sys, os
import vars, state, builder
from log import debug, debug2, debug3, warn

CLEAN = 0
DIRTY = 1

# FIXME: sanitize the return values of this function into a tuple instead.
def isdirty(f, depth, expect_stamp):
    assert(isinstance(expect_stamp, state.Stamp))
    debug('%s?%s\n', depth, f.name)

    debug3('%sexpect: %r\n', depth, expect_stamp)
    debug3('%sold:    %r\n', depth, f.stamp)

    if not f.is_generated and expect_stamp.is_none() and f.exists():
        debug('%s-- CLEAN (static)\n', depth)
        return CLEAN
    if f.exitcode:
        debug('%s-- DIRTY (failed last time)\n', depth)
        return DIRTY
    if not expect_stamp.is_missing() and f.stamp.is_missing() and not f.stamp.runid():
        debug('%s-- DIRTY (never built)\n', depth)
        return DIRTY
    if f.stamp.is_old():
        debug('%s-- DIRTY (from old redo)\n', depth)
        return DIRTY
    if not f.stamp or f.stamp.is_none():
        debug('%s-- DIRTY (no stamp)\n', depth)
        return DIRTY

    newstamp = f.read_stamp()

    debug3('%snew:    %r\n', depth, newstamp)

    if newstamp.is_override_or_missing(f) and not newstamp.is_missing():
        if vars.OVERWRITE:
            debug('%s-- DIRTY (override)\n', depth)
            return DIRTY
        else:
            debug('%s-- CLEAN (override)\n', depth)
            return CLEAN

    if newstamp.is_stamp_dirty(f):
        if newstamp.is_missing():
            debug('%s-- DIRTY (missing)\n', depth)
        else:
            debug('%s-- DIRTY (mtime)\n', depth)
        return [f] if f.stamp.is_csum() else DIRTY

    must_build = []
    for stamp2, f2 in f.deps:
        dirty = CLEAN

        if f2 == state.ALWAYS:
            if f.stamp_mtime >= vars.RUNID:
                # has already been checked during this session
                debug('%s-- CLEAN (always, checked)\n', depth)
            else:
                debug('%s-- DIRTY (always)\n', depth)
                dirty = DIRTY
        else:
            f2 = state.File(f2, f.dir)
            sub = isdirty(f2, depth = depth + '  ',
                          expect_stamp = stamp2)
            if sub:
                debug('%s-- DIRTY (sub)\n', depth)
                dirty = sub

        if not f.stamp.is_csum():
            # f is a "normal" target: dirty f2 means f is instantly dirty
            if dirty:
                # if dirty==DIRTY, this means f is definitely dirty.
                # if dirty==[...], it's a list of the uncertain children.
                return dirty
        else:
            # f is "checksummable": dirty f2 means f needs to redo,
            # but f might turn out to be clean after that (ie. our parent
            # might not be dirty).
            if dirty == DIRTY:
                # f2 is definitely dirty, so f definitely needs to
                # redo.  However, after that, f might turn out to be
                # unchanged.
                return [f]
            elif isinstance(dirty, list):
                # our child f2 might be dirty, but it's not sure yet.  It's
                # given us a list of targets we have to redo in order to
                # be sure.
                must_build += dirty

    if must_build:
        # f is *maybe* dirty because at least one of its children is maybe
        # dirty.  must_build has accumulated a list of "topmost" uncertain
        # objects in the tree.  If we build all those, we can then
        # redo-ifchange f and it won't have any uncertainty next time.
        return must_build

    if expect_stamp.is_dirty(f):
        # This must be after we checked the children. Before, we didn't knew
        # if the current target was dirty or not
        debug('%s-- DIRTY (parent)\n', depth)
        return DIRTY

    # if we get here, it's because the target is clean
    debug2('%s-- CLEAN (dropped off)\n', depth)
    return CLEAN


