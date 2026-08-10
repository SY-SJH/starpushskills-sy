#!/usr/bin/env python3
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    drafts = root / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    print(str(drafts))


if __name__ == "__main__":
    main()
