#!/usr/bin/env python3
"""paylink — generate Base USDC payment URIs + optional Shieldz unlocks (no API key for links).

Stdlib-only Python 3. Agents use this to mint shareable tip/pay links that settle to a
receive-only wallet on Base. Never asks for private keys.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from urllib.parse import quote, urlencode

CHAIN_ID_BASE = 8453
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDC_DECIMALS = 6
DEFAULT_TREASURY = "0xbAd41cF0f0d5442f9A53630F8081BFd257DA019b"
SHIELDZ_TIP_API = "https://shieldz.cash/api/v1/tip-jars"
SHIELDZ_UNLOCK_API = "https://shieldz.cash/api/v1/unlocks"
KNOWN_TIP_JAR = "https://shieldz.cash/tip/tip-d2599a4d16a6f4b0"


def _normalize_address(addr: str) -> str:
    a = addr.strip()
    if not a.startswith("0x") or len(a) != 42:
        raise ValueError(f"Expected 0x-prefixed 40-hex address, got: {addr!r}")
    int(a[2:], 16)
    return a


def usd_to_atomic(amount_usd: str | Decimal) -> int:
    try:
        d = Decimal(str(amount_usd))
    except InvalidOperation as e:
        raise ValueError(f"Invalid USD amount: {amount_usd!r}") from e
    if d < 0:
        raise ValueError("Amount must be >= 0")
    atomic = (d * (Decimal(10) ** USDC_DECIMALS)).quantize(Decimal(1), rounding=ROUND_DOWN)
    return int(atomic)


def eip681_usdc_transfer(to: str, amount_usd: str | Decimal | None = None) -> str:
    """EIP-681 URI for ERC-20 transfer of native USDC on Base."""
    to = _normalize_address(to)
    base = f"ethereum:{USDC_BASE}@{CHAIN_ID_BASE}/transfer"
    params: dict[str, str] = {"address": to}
    if amount_usd is not None and str(amount_usd) != "":
        params["uint256"] = str(usd_to_atomic(amount_usd))
    return f"{base}?{urlencode(params)}"


def metamask_deeplink(eip681: str) -> str:
    # MetaMask mobile open deeplink for ethereum: URIs
    return f"https://metamask.app.link/send/{quote(eip681, safe='')}"


def rainbow_deeplink(eip681: str) -> str:
    return f"https://rnbwapp.com/send?{urlencode({'uri': eip681})}"


def basescan_address(to: str) -> str:
    return f"https://basescan.org/address/{_normalize_address(to)}"


def coinbase_wallet_send_hint(to: str, amount_usd: str | None) -> str:
    # Coinbase Wallet has no stable public USDC deep-link; give honest instructions.
    amt = f" for ${amount_usd} USDC" if amount_usd else ""
    return (
        f"Open Coinbase Wallet → Send → paste {_normalize_address(to)} → "
        f"pick USDC on Base{amt}."
    )


def build_bundle(
    to: str,
    amount_usd: str | None = None,
    tip_jar: str | None = KNOWN_TIP_JAR,
) -> dict:
    to = _normalize_address(to)
    eip = eip681_usdc_transfer(to, amount_usd)
    bundle = {
        "chain": "base",
        "chain_id": CHAIN_ID_BASE,
        "asset": "USDC",
        "token": USDC_BASE,
        "to": to,
        "amount_usd": amount_usd,
        "amount_atomic": usd_to_atomic(amount_usd) if amount_usd else None,
        "eip681": eip,
        "metamask_deeplink": metamask_deeplink(eip),
        "rainbow_hint": rainbow_deeplink(eip),
        "basescan": basescan_address(to),
        "coinbase_wallet": coinbase_wallet_send_hint(to, amount_usd),
        "shieldz_tip_jar": tip_jar,
        "notes": [
            "EIP-681 works in wallets that support ethereum: URIs (MetaMask mobile, Rainbow, etc.).",
            "Receiving USDC on Base does not require the recipient to hold ETH.",
            "Prefer Shieldz tip jar for pay-what-you-want; use EIP-681 when the payer wants a fixed amount.",
        ],
    }
    return bundle


def _http_json(url: str, payload: dict, timeout: float = 30.0) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "paylink/1.0 (+https://github.com/filip-study/base-usdc-paylink)",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {url}: {detail}") from e


def create_tip_jar(
    address: str,
    title: str,
    description: str,
    brand: str,
    amounts_cents: list[int],
) -> dict:
    return _http_json(
        SHIELDZ_TIP_API,
        {
            "settlement": {
                "chain": "BASE",
                "asset": "USDC",
                "address": _normalize_address(address),
            },
            "title": title,
            "description": description,
            "suggested_amounts_usd_cents": amounts_cents,
            "brand": brand,
        },
    )


def create_unlock(
    address: str,
    price_usd_cents: int,
    payload: str,
    title: str,
    description: str,
) -> dict:
    return _http_json(
        SHIELDZ_UNLOCK_API,
        {
            "to": _normalize_address(address),
            "price_usd_cents": price_usd_cents,
            "payload": payload,
            "title": title,
            "description": description,
            "aup_accepted": True,
            "chain": "BASE",
            "asset": "USDC",
        },
    )


def cmd_link(args: argparse.Namespace) -> int:
    bundle = build_bundle(args.to, args.amount, tip_jar=args.tip_jar or KNOWN_TIP_JAR)
    if args.json:
        print(json.dumps(bundle, indent=2))
        return 0
    print(f"Base USDC paylink → {bundle['to']}")
    if bundle["amount_usd"]:
        print(f"  Amount : ${bundle['amount_usd']} USDC ({bundle['amount_atomic']} atomic)")
    else:
        print("  Amount : (open — payer chooses)")
    print(f"  EIP-681 : {bundle['eip681']}")
    print(f"  MetaMask: {bundle['metamask_deeplink']}")
    print(f"  Basescan: {bundle['basescan']}")
    if bundle["shieldz_tip_jar"]:
        print(f"  Tip jar : {bundle['shieldz_tip_jar']}")
    print(f"  Coinbase: {bundle['coinbase_wallet']}")
    return 0


def cmd_tip(args: argparse.Namespace) -> int:
    amounts = [int(x) for x in args.amounts.split(",") if x.strip()]
    result = create_tip_jar(
        args.to,
        title=args.title,
        description=args.description,
        brand=args.brand,
        amounts_cents=amounts,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Shieldz tip jar created (or reused):")
        print(f"  url: {result.get('url')}")
        if result.get("manage_token"):
            print(f"  manage_token: {result['manage_token']}  (SAVE THIS — shown once)")
        elif result.get("manage_note"):
            print(f"  note: {result['manage_note']}")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    with open(args.file, "r", encoding="utf-8") as f:
        payload = f.read()
    if not payload.strip():
        print("paylink error: payload file is empty", file=sys.stderr)
        return 1
    result = create_unlock(
        args.to,
        price_usd_cents=args.price_cents,
        payload=payload,
        title=args.title,
        description=args.description,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Shieldz unlock created:")
        print(f"  url: {result.get('url')}")
        if result.get("manage_token"):
            print(f"  manage_token: {result['manage_token']}  (SAVE THIS — shown once)")
        for k in ("price_usd_cents", "title", "slug"):
            if k in result:
                print(f"  {k}: {result[k]}")
    return 0


def cmd_readme_block(args: argparse.Namespace) -> int:
    tip = args.tip_jar or KNOWN_TIP_JAR
    unlock = args.unlock or ""
    to = _normalize_address(args.to)
    lines = [
        "## Support / pay (Base USDC)",
        "",
        f"- **Treasury:** `{to}`",
        f"- **Tip jar (pay-what-you-want):** {tip}",
    ]
    if unlock:
        lines.append(f"- **Unlock (fixed price):** {unlock}")
    lines += [
        "",
        "Generate a fixed-amount EIP-681 link:",
        "",
        "```bash",
        f"python3 paylink.py link --to {to} --amount 5",
        "```",
        "",
    ]
    print("\n".join(lines))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="paylink",
        description="Generate Base USDC payment links and create Shieldz tip/unlock pipes.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("link", help="Print EIP-681 + wallet deep links for Base USDC")
    pl.add_argument("--to", default=DEFAULT_TREASURY, help="Receive address")
    pl.add_argument("--amount", default=None, help="USD amount (e.g. 5 or 7.50)")
    pl.add_argument("--tip-jar", default=KNOWN_TIP_JAR, help="Optional Shieldz tip URL to include")
    pl.add_argument("--json", action="store_true")
    pl.set_defaults(func=cmd_link)

    pt = sub.add_parser("tip", help="Create/reuse a Shieldz tip jar for an address")
    pt.add_argument("--to", default=DEFAULT_TREASURY)
    pt.add_argument("--title", default="Tip jar — Base USDC")
    pt.add_argument("--description", default="Thanks for the tip.")
    pt.add_argument("--brand", default="paylink")
    pt.add_argument("--amounts", default="100,300,500,1000", help="USD cents, comma-separated")
    pt.add_argument("--json", action="store_true")
    pt.set_defaults(func=cmd_tip)

    pu = sub.add_parser("unlock", help="Create a Shieldz pay-to-unlock from a file")
    pu.add_argument("--to", default=DEFAULT_TREASURY)
    pu.add_argument("--file", required=True, help="Path to payload (markdown/text)")
    pu.add_argument("--price-cents", type=int, default=700, help="Price in USD cents (default 700 = $7)")
    pu.add_argument("--title", required=True)
    pu.add_argument("--description", default="Digital good — unlocks after Base USDC payment.")
    pu.add_argument("--json", action="store_true")
    pu.set_defaults(func=cmd_unlock)

    pr = sub.add_parser("readme-block", help="Print a ready-to-paste README money section")
    pr.add_argument("--to", default=DEFAULT_TREASURY)
    pr.add_argument("--tip-jar", default=KNOWN_TIP_JAR)
    pr.add_argument("--unlock", default="")
    pr.set_defaults(func=cmd_readme_block)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as e:
        print(f"paylink error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
