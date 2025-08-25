import os
import smtplib
import sys

import pytest

# Ensure project root (backend folder) is on sys.path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(autouse=True)
def mock_smtp(monkeypatch):
    """Mock smtplib.SMTP so tests never attempt real SMTP connections.

    Captures sent messages in the returned list for optional assertions.
    """
    sent_messages = []

    class DummySMTP:
        def __init__(self, host, port, *args, **kwargs):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def send_message(self, msg):
            sent_messages.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", DummySMTP)
    return sent_messages
