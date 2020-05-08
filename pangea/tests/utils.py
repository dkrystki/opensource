import sys


def pg(*args):
    sys.argv = ("pangea",) + args
    from pangea import scripts

    scripts._main()
    sys.argv = []
