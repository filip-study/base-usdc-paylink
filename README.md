# base-usdc-paylink

**Mint Base USDC payment links in one command.** Stdlib Python CLI for agents and humans who need shareable EIP-681 URIs, MetaMask deeplinks, and Shieldz tip/unlock helpers — **no API key for link generation, no wallet, no private keys**.

Complements [`tipcheck`](https://github.com/filip-study/base-usdc-tip-kit) (Pete): that tool *monitors* a treasury; `paylink` *creates* what the payer opens.

## Install / run

```bash
git clone https://github.com/filip-study/base-usdc-paylink.git
cd base-usdc-paylink
python3 paylink.py link --amount 5
python3 paylink.py link --amount 7.5 --json
python3 test_paylink.py
```

Requirements: **Python 3.9+**, network only when creating Shieldz tip/unlock. Link generation is offline.

## Commands

| Command | What it does |
|---------|----------------|
| `link` | EIP-681 + MetaMask deeplink + Basescan + tip jar |
| `tip` | Create/reuse a Shieldz tip jar for an address |
| `unlock` | Create a Shieldz pay-to-unlock from a file |
| `readme-block` | Print a paste-ready README money section |

### Examples

```bash
# Fixed $5 USDC on Base → default treasury
python3 paylink.py link --amount 5

# Custom receive address
python3 paylink.py link --to 0xYourAddress --amount 3 --json

# Paste-ready README footer
python3 paylink.py readme-block --unlock https://shieldz.cash/unlock/2B-pnOcAsqSdaw7IMmSL

# Sell a markdown file as a $5 unlock
python3 paylink.py unlock \
  --file ./product.md \
  --price-cents 500 \
  --title "My micro-product" \
  --description "One-sentence pitch."
```

## Support this tool (Base USDC)

| | |
|---|---|
| **Treasury** | `0xbAd41cF0f0d5442f9A53630F8081BFd257DA019b` |
| **Tip jar** | https://shieldz.cash/tip/tip-d2599a4d16a6f4b0 |
| **Agent Receive Pack ($5 unlock)** | https://shieldz.cash/unlock/2B-pnOcAsqSdaw7IMmSL |

If `paylink` saved you from hand-rolling EIP-681 strings, tip a coffee — or unlock Nancy's fuller receive pack (README blocks, unlock recipes, ledger stub).

## How EIP-681 links work

```
ethereum:<USDC_ON_BASE>@8453/transfer?address=<TO>&uint256=<ATOMIC>
```

- Native USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- 6 decimals → $5 = `5000000` atomic units
- Wallets that understand `ethereum:` URIs (MetaMask mobile, Rainbow, …) can open the deeplink
- Coinbase Wallet: use the honest manual send steps printed by the CLI (no fake deep link)

## Pair with tipcheck

After someone says they paid:

```bash
python3 tipcheck.py 0xbAd41cF0f0d5442f9A53630F8081BFd257DA019b
```

## License

MIT — see [`LICENSE`](./LICENSE).

## Disclaimer

Public link generation and optional Shieldz API calls only. Never asks for private keys. Not financial advice. Legal use only; no impersonation.
