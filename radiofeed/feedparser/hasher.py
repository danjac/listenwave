from __future__ import annotations

import hashlib


def hash(content: bytes) -> str:
    """Hashes content to a hex string."""
    return hashlib.sha256(content).hexdigest()