"""Allow ``python -m monad`` when run from the parent directory."""

from main import main

if __name__ == "__main__":
    raise SystemExit(main())
