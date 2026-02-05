"""Simple PID-file based single-instance lock.

This is intentionally minimal to avoid extra dependencies and works cross-platform.
It will create a PID file (config.PID_FILE) containing the process PID and
refuse to start if another live PID is present. Stale PID files are removed.
"""

import os
from pathlib import Path
import errno


class SingleInstance:
    def __init__(self, lockfile: Path):
        self.lockfile = Path(lockfile)

    def acquire(self):
        # If lock exists check whether process is running
        if self.lockfile.exists():
            try:
                pid_text = self.lockfile.read_text().strip()
                pid = int(pid_text)
            except Exception:
                # Corrupt/stale lock file
                try:
                    self.lockfile.unlink()
                except Exception:
                    pass
            else:
                # Check if process is running
                try:
                    os.kill(pid, 0)
                except OSError:
                    # Process not running -> stale lock
                    try:
                        self.lockfile.unlink()
                    except Exception:
                        pass
                else:
                    raise RuntimeError(f"Another instance is running (pid={pid}).")

        # Create lock file and write own pid
        try:
            self.lockfile.write_text(str(os.getpid()))
        except Exception as e:
            raise RuntimeError(f"Unable to create lock file {self.lockfile}: {e}")

    def release(self):
        try:
            if self.lockfile.exists():
                try:
                    pid_text = self.lockfile.read_text().strip()
                    if pid_text and int(pid_text) == os.getpid():
                        self.lockfile.unlink()
                except Exception:
                    # Best-effort: try to remove anyway
                    try:
                        self.lockfile.unlink()
                    except Exception:
                        pass
        except Exception:
            pass
