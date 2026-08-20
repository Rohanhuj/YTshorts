"""Fail CI when tracked project files contain common credential signatures."""

from shorts_automation.observability.secret_scan import main

if __name__ == "__main__":
    raise SystemExit(main())
