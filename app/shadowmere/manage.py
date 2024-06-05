#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    if os.getenv("DEBUG", "NO").lower() in ("on", "true", "y", "yes"):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path / "shadowmere"))
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
