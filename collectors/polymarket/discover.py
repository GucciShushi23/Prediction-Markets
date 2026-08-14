"""Fetch active Polymarket markets and print a compact, pickable list.

Run:  py -m uv run python collectors/polymarket/discover.py > markets_list.txt
"""
import json
import httpx

GAMMA = "https://gamma-api.polymarket.com"


def fetch(limit: int = 500) -> list:
    r = httpx.get(
        f"{GAMMA}/markets",
        params={"limit": limit, "closed": "false", "order": "volumeNum", "ascending": "false"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def parse_tokens(raw):
    """clobTokenIds comes back as a JSON string, not a list. Parse it."""
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    return raw or []


if __name__ == "__main__":
    markets = fetch()
    rows = []
    for m in markets:
        tokens = parse_tokens(m.get("clobTokenIds"))
        if not tokens:
            continue
        vol = m.get("volumeNum") or 0
        try:
            vol = float(vol)
        except (TypeError, ValueError):
            vol = 0.0
        rows.append({
            "vol": vol,
            "question": m.get("question", "???"),
            "tick": m.get("orderPriceMinTickSize"),
            "negrisk": m.get("negRisk", False),
            "n_outcomes": len(tokens),
            "tokens": tokens,
        })

    # sort ascending so the low-volume ones you want are at the TOP
    rows.sort(key=lambda r: r["vol"])

    for r in rows:
        flag = " [NEG-RISK/MULTI]" if r["negrisk"] or r["n_outcomes"] > 2 else ""
        print(f"VOL={r['vol']:>14,.0f} | tick={r['tick']} | {r['question']}{flag}")
        print(f"    tokens={r['tokens']}")
        print()