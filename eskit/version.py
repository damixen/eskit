import subprocess

__version__ = "0.4.1"
__cache_format_version__ = 20260718


def get_git_info():
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short=8", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        return {
            "branch": branch or None,
            "commit": commit or None,
        }

    except (OSError, subprocess.CalledProcessError):
        return {}
