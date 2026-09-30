# eskit/log.py

import logging
import sys


def configure_logging(verbose=False, debug=False):
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="%(levelname)s [%(name)s]: %(message)s",
        force=True,       # Python 3.8+
    )

    # Set logging level for specific libraries to WARNING to reduce noise
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)