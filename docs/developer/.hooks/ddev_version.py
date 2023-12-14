import os
import subprocess
from functools import cache
from pathlib import Path

MARKER = '<docs-insert-ddev-version>'
SEMVER_PARTS = 3

# Ignore the current documentation environment so that the version
# command can execute as usual in the default build environment
os.environ.pop('HATCH_ENV_ACTIVE', None)


@cache
def get_latest_version():
    """This returns the latest version of ddev."""
    ddev_root = Path.cwd() / 'ddev'
    print("Path: " + str(ddev_root))
    print("process: " + subprocess.check_output(['ls', '-l', str(ddev_root)], cwd=str(ddev_root)).decode('utf-8').strip())
    output = subprocess.check_output(['hatch', 'version'], cwd=str(ddev_root)).decode('utf-8').strip()
    print("output: " + output)

    version = output.replace('dev', '')

    print("version: " + version)
    print(version.split('.'))
    parts = list(map(int, version.split('.')))
    major, minor, patch = parts[:SEMVER_PARTS]
    if len(parts) > SEMVER_PARTS:
        patch -= 1

    return f'{major}.{minor}.{patch}'


def on_page_read_source(page, config):
    """This inserts the latest version of ddev."""
    with open(page.file.abs_src_path, encoding='utf-8') as f:
        return f.read().replace(MARKER, get_latest_version())
