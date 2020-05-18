import sys


def command(*args):
    sys.argv = ("pangea",) + args
    from pangea import scripts

    scripts._main()
    sys.argv = []
