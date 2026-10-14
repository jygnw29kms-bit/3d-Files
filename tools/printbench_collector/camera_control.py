"""Explicit, expiring local camera consent; telemetry does not depend on it."""
import argparse
import json
import os
import time
from pathlib import Path

LEASE = Path(__file__).resolve().parent / "media" / "camera-request.json"


def enabled(now=None):
    now = time.time() if now is None else now
    try:
        expires = float(json.loads(LEASE.read_text(encoding="utf-8"))["expires"])
        return now < expires <= now + 8 * 3600
    except (OSError, ValueError, TypeError, KeyError):
        return False


def request(minutes=30):
    if not 1 <= minutes <= 480:
        raise ValueError("Camera duration must be 1–480 minutes")
    LEASE.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEASE.with_name(LEASE.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"expires": time.time() + minutes * 60}), encoding="utf-8")
    tmp.replace(LEASE)


def disable():
    LEASE.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["on", "off", "status"])
    parser.add_argument("--minutes", type=int, default=30)
    args = parser.parse_args()
    if args.action == "on": request(args.minutes)
    elif args.action == "off": disable()
    else: print("Camera on" if enabled() else "Camera off")
