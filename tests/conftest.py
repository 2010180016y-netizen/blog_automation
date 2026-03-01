import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_OS = os.path.join(ROOT, "content_os")
if CONTENT_OS not in sys.path:
    sys.path.insert(0, CONTENT_OS)

TESTS_DIR = os.path.join(ROOT, "tests")
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)
