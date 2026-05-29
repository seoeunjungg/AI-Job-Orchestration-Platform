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


def run_fail_once(payload: dict):
    attempt = payload.get("_attempt", 1)
    if attempt == 1:
        raise RuntimeError("simulated first-attempt failure")

    return {
        "message": "succeeded after retry",
        "attempt": attempt,
    }


HANDLERS = {
    "echo": run_echo,
    "sleep": run_sleep,
    "fail_once": run_fail_once,
}
