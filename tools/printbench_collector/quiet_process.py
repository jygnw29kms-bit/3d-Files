"""Keep Windows child processes hidden, including when launched by pythonw."""
import os
import subprocess


def options():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
