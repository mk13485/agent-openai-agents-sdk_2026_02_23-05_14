import shlex
import subprocess
from typing import Any, Dict, List, Union


def run(cmd: Union[str, List[str]], timeout: int = 60, check: bool = False) -> Dict[str, Any]:
    try:
        args = shlex.split(cmd) if isinstance(cmd, str) else cmd
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "error": "timeout",
            "stdout": e.stdout or "",
            "stderr": e.stderr or "",
        }
    except subprocess.CalledProcessError as e:
        return {
            "ok": False,
            "error": "non-zero exit",
            "returncode": e.returncode,
            "stdout": e.stdout or "",
            "stderr": e.stderr or "",
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
