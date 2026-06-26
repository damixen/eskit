import subprocess
import shlex
import os
import errno
import signal

class AsynchronousProcess:
    def __init__(self, host_cfg):
        self.host_cfg = host_cfg
        self.client = None
        self.name = "AsynchronousProcess"

    def connect(self):
        pass

    def run(self, cmd):

        result = subprocess.Popen(
            shlex.split(cmd, posix=True),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return result

    def check(self, pid):
        if pid < 0:
            return False
        try:
            # Signal 0 does nothing but checks if the PID exists
            os.kill(pid, 0)
        except OSError as e:
            # ESRCH means no such process exists
            if e.errno == errno.ESRCH:
                return False
            # EPERM means the process exists but you lack permission to signal it
            elif e.errno == errno.EPERM:
                return True
            else:
                # Other errors (should be rare)
                return False
        else:
            return True

    def kill(self, pid):
        try:
            # SIGKILL forces the process to close immediately
            os.kill(pid, signal.SIGKILL)
            print(f"Process {pid} killed.")
        except ProcessLookupError:
            print(f"PID {pid} does not exist.")
        except PermissionError:
            print(f"Insufficient permissions to kill PID {pid}.")

    def close(self):
        pass


class SynchronousProcess:
    def __init__(self, shell=False):
        self.name = "SynchronousProcess"
        self.shell = shell

    def connect(self):
        pass

    def run(self, cmd):

        if self.shell:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        else:
            result = subprocess.run(
                shlex.split(cmd, posix=True), capture_output=True, text=True
            )
        return result.stdout

    def close(self):
        pass
