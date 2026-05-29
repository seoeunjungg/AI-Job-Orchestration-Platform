# handlers.py: worker executes workload (functions that perform each job type)

import time


def run_echo(payload: dict):
    return payload


def run_sleep(payload: dict):
    seconds = payload.get("seconds", 1)
    if not isinstance(seconds, int | float) or seconds < 0:
        raise ValueError("seconds must be a non-negative number")

    time.sleep(seconds)

    return {
        "message": f"slept for {seconds} seconds"
    }

HANDLERS = {
    "echo": run_echo,
    "sleep": run_sleep,
}
