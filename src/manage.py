#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from typing import NoReturn


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoflix.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        error_message = (
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )
        raise ImportError(error_message) from exc
    
    execute_from_command_line(sys.argv)


def handle_exception(exc: Exception) -> NoReturn:
    """Handle uncaught exceptions with custom formatting."""
    print(f"Error: {exc}", file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        handle_exception(exc)
