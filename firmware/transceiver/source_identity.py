#!/usr/bin/env python3
"""Capture source identity BEFORE export to a build host; never infer from that host."""
import argparse
import json
from pathlib import Path
import subprocess


def identity(root):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    revision = git('rev-parse', 'HEAD')
    dirty = bool(git('status', '--porcelain', '--untracked-files=all'))
    return {'git_sha': revision, 'dirty': int(dirty),
            'cmake_args': ['-DEMBER_GIT_REVISION=' + revision,
                           '-DEMBER_GIT_DIRTY=' + str(int(dirty))]}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cmake-args', action='store_true', help='Print one CMake argument per line')
    args = p.parse_args()
    result = identity(Path(__file__).resolve().parents[2])
    print('\n'.join(result['cmake_args']) if args.cmake_args else json.dumps(result, indent=2))
