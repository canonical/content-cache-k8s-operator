#!/usr/bin/env python3

# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import os
from io import StringIO
from typing import Generator

"""Short module for file reverse reading."""


def readlines_reverse(qfile) -> Generator[int, None, None]:
    """Read the lines of a file in reverse order in a lazy way."""
    with qfile:
        qfile.seek(0, os.SEEK_END)
        position = qfile.tell() - 2
        line = StringIO("")
        while position >= 0:
            qfile.seek(position)
            next_char = qfile.read(1)
            if next_char == "\n":
                yield line.getvalue()[::-1]
                line = StringIO("")
            else:
                line.write(next_char)
            position -= 1
        yield line.getvalue()[::-1]
