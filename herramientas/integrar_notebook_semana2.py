"""Rebuild the standalone Week 2 notebook from its English delivery source package.

Historical source, configuration and attribution remain in the Git history and
project records. This builder assembles files; it does not train models.
"""
from build_delivery_notebooks import build

if __name__ == "__main__":
    print(build(2))
