"""Pytest configuration.

Adds the add-in root to ``sys.path`` so the ``lib`` package is importable, and
installs the ``adsk`` stub before any test imports the modeler.
"""

import os
import sys

# The add-in root is the parent of this tests/ directory.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Install the adsk stub globally so `import adsk.core` works in tests.
from . import adsk_stub  # noqa: E402

adsk_stub.install()
