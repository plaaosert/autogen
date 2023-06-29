from enum import Enum


class LOGLEVEL(Enum):
    CRITICAL = 0        # Always, even when silent
    INFO_QUIET = 1      # Enabled as long as not silent
    INFO = 2            # Enabled if not silent or quiet (default)
    DEBUG = 3           # Only enabled if debug


CURRENT_LOGLEVEL = LOGLEVEL.INFO


def is_debug():
    return CURRENT_LOGLEVEL.value >= LOGLEVEL.DEBUG.value


def get_loglevel():
    return CURRENT_LOGLEVEL.value


def set_loglevel(loglevel: LOGLEVEL):
    global CURRENT_LOGLEVEL

    CURRENT_LOGLEVEL = loglevel


def log(loglevel: LOGLEVEL, *objects, prefix="\u001b[0m[ ]", suffix="\u001b[0m"):
    if CURRENT_LOGLEVEL.value >= loglevel.value:
        text = " ".join(str(o) for o in objects)
        print(prefix + " [{:^10}] ".format(loglevel.name) + text + suffix)


def log_error(loglevel, *objects):
    log(loglevel, *objects, prefix="\u001b[31;1m[!]", suffix="\u001b[0m")


def log_failure(loglevel, *objects):
    log(loglevel, *objects, prefix="\u001b[31m[-]", suffix="\u001b[0m")


def log_success(loglevel, *objects):
    log(loglevel, *objects, prefix="\u001b[32;1m[+]", suffix="\u001b[0m")


def log_info(loglevel, *objects):
    log(loglevel, *objects, prefix="\u001b[0m[.]", suffix="\u001b[0m")
