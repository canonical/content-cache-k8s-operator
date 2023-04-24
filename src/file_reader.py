"""Short module for file reverse reading."""

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import os
from io import StringIO
from typing import Generator


def readlines_reverse(qfile) -> Generator[int, None, None]:
    """Read the lines of a file in reverse order in a lazy way.

    Args:
        qfile: File in StringIO format.

    Yields:
        A row from the read file.
    """
    with qfile:
        qfile.seek(0, os.SEEK_END)
        position = qfile.tell()
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
