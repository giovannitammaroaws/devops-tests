#!/usr/bin/env python3
"""Run Trivy misconfiguration scan as a pre-push hook.

Priority:
1. Use local `trivy` binary if available.
2. Fallback to Docker image `aquasec/trivy:0.69.3`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> int:
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd))
    return proc.returncode


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scan_args = [
        "fs",
        "--scanners",
        "misconfig",
        "--exit-code",
        "1",
        "--severity",
        "HIGH,CRITICAL",
        ".",
    ]

    trivy = shutil.which("trivy")
    if trivy:
        return run([trivy, *scan_args], repo_root)

    docker = shutil.which("docker")
    if not docker:
        print("ERROR: neither `trivy` nor `docker` is available in PATH.")
        print("Install Trivy or Docker Desktop to enable the pre-push scan.")
        return 1

    image = os.environ.get("TRIVY_IMAGE", "aquasec/trivy:0.69.3")
    mount = f"{repo_root}:/work"
    docker_cmd = [docker, "run", "--rm", "-v", mount, "-w", "/work", image, *scan_args]
    return run(docker_cmd, repo_root)


if __name__ == "__main__":
    sys.exit(main())
