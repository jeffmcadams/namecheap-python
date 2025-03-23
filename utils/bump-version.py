#!/usr/bin/env python3
"""
Utility to bump the package version using GitHub Actions workflow
"""

import subprocess
import sys


def main() -> None:
    """Run the GitHub Actions workflow to bump the package version"""
    release_type = "patch"
    if len(sys.argv) > 1 and sys.argv[1] in ["patch", "minor", "major"]:
        release_type = sys.argv[1]

    print(f"Running version bump workflow with version_part={release_type}")
    subprocess.run(
        f'gh workflow run "Bump Version and Release" -f version_part={release_type}',
        shell=True,
        check=True,
    )


if __name__ == "__main__":
    main()
