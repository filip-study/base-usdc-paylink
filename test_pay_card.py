#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(*args: str) -> str:
    r = subprocess.run(
        [sys.executable, str(HERE / "pay_card.py"), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return r.stdout


def main() -> None:
    j = json.loads(run("--json", "--amount", "5"))
    assert j["atomic"] == 5_000_000
    assert "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913@8453/transfer" in j["eip681"]
    assert j["to"].startswith("0xbAd41")
    html = run("--amount", "3", "--title", "Smoke")
    assert "ethereum:" in html and "MetaMask" in html and "Smoke" in html
    print("PASS", j["eip681"][:60] + "…")


if __name__ == "__main__":
    main()
