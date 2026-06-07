"""Ensure real anthropic module is used in control-plane tests even when test_main.py
stubs it out in the same pytest session (test isolation fix)."""
import sys


def pytest_configure(config):
    """Remove any stub anthropic module before control-plane collection."""
    stub = sys.modules.get("anthropic")
    if stub is not None and not hasattr(stub, "BadRequestError"):
        # It's the thin stub from tests/test_main.py — remove it so the
        # real package gets imported when langchain_anthropic loads.
        del sys.modules["anthropic"]
        # Also clear any langchain_anthropic sub-modules that may have
        # been partially imported using the stub.
        for key in list(sys.modules):
            if key.startswith("langchain_anthropic"):
                del sys.modules[key]
