#!/usr/bin/env python3
"""A program that generates Makefiles given the lab configuration in a target directory."""
import sys

try:
    import lab_config as cfg
except ImportError as e:
    from os.path import join, dirname

    sys.path.append(join(join(dirname(__file__), '..'), '.config'))
    import lab_config as cfg
from ccsrcutilities import mk_makefiles


def main():
    """Create a root level and part level makefile for a 120 lab."""
    if len(sys.argv) < 2:
        print('Provide a target directory.')
        sys.exit(1)
    mk_makefiles(sys.argv[1], cfg)


if __name__ == '__main__':
    main()
