"""
Language parsers for code analysis.

This module provides the interface and implementations for parsing different programming languages.
"""

import importlib
from typing import Dict, Optional, Type

from .base import LanguageParser

# Registry of parsers for different languages
_PARSERS: Dict[str, Type[LanguageParser]] = {}


def register_parser(language: str):
    """
    Decorator to register a language parser.

    Args:
        language: The language identifier (e.g., "python", "javascript")

    Returns:
        A decorator function that registers the parser class
    """

    def decorator(cls):
        _PARSERS[language] = cls
        return cls

    return decorator


def get_parser_for_language(language: str) -> Optional[LanguageParser]:
    """
    Get a parser instance for the specified language.

    Args:
        language: The language identifier

    Returns:
        An instance of the appropriate language parser, or None if not supported
    """
    if language not in _PARSERS:
        # Try to dynamically import the language module
        try:
            importlib.import_module(f".{language}", package=__name__)
        except ImportError:
            return None

    if language in _PARSERS:
        return _PARSERS[language]()
    return None


__all__ = ["LanguageParser", "register_parser", "get_parser_for_language"]
