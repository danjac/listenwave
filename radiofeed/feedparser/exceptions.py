from __future__ import annotations


class NotModified(ValueError):
    """RSS feed has not been modified since last update."""


class DuplicateFeed(ValueError):
    """Another identical podcast exists in the database."""


class RssParserError(ValueError):
    """Broken XML syntax or missing/invalid required attributes."""
