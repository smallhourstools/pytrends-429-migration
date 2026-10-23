"""Read Google Trends interest over time with pytrends, waiting after a 429 and caching on disk.

Usage:
    python3 trends_retry.py "cold brew" "iced tea" --geo US --timeframe "today 12-m"

One term per request (Google rejects many terms at once more often), a pause between terms, and a longer
wait after every 429. Results are cached per term, geo and timeframe, so a rerun does not ask Google
again for what it already gave you.
"""
import argparse
import hashlib
import json
import pathlib
import random
import sys
import time

from pytrends.exceptions import ResponseError
from pytrends.request import TrendReq

CACHE_DIR = pathlib.Path(".trends-cache")
MAX_TRIES = 5
FIRST_WAIT = 30      # seconds after the first 429
PAUSE_BETWEEN = 10   # seconds between different terms
CACHE_HOURS = 24


def is_429(err):
    text = str(err)
    return "429" in text or "TooManyRequests" in type(err).__name__ or "too many" in text.lower()


def cache_path(term, geo, timeframe):
    key = hashlib.sha1(f"{term}|{geo}|{timeframe}".encode()).hexdigest()[:16]
    return CACHE_DIR / f"{key}.json"


def read_cache(path):
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > CACHE_HOURS * 3600:
        return None
    return json.loads(path.read_text())


def fetch_term(term, geo="", timeframe="today 12-m", log=print):
    """Return a list of {"date", "value", "isPartial"} for one term. Raises after MAX_TRIES refusals."""
    path = cache_path(term, geo, timeframe)
    cached = read_cache(path)
    if cached is not None:
        log(f"cache hit: {term}")
        return cached

    wait = FIRST_WAIT
    for attempt in range(1, MAX_TRIES + 1):
        try:
            client = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
            client.build_payload([term], timeframe=timeframe, geo=geo)
            frame = client.interest_over_time()
            rows = []
            if not frame.empty:
                for stamp, row in frame.iterrows():
                    rows.append({
                        "date": stamp.strftime("%Y-%m-%d"),
                        "value": int(row[term]),
                        "isPartial": bool(row.get("isPartial", False)),
                    })
            CACHE_DIR.mkdir(exist_ok=True)
            path.write_text(json.dumps(rows))
            return rows
        except Exception as err:  # pytrends raises ResponseError, requests errors, and plain exceptions
            if not (isinstance(err, ResponseError) and is_429(err)) and not is_429(err):
                raise
            if attempt == MAX_TRIES:
                raise
            pause = wait + random.uniform(0, wait * 0.2)
            log(f"429 for '{term}' (try {attempt}/{MAX_TRIES}). Waiting {pause:.0f}s.")
            time.sleep(pause)
            wait *= 2
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("terms", nargs="+")
    parser.add_argument("--geo", default="")
    parser.add_argument("--timeframe", default="today 12-m")
    args = parser.parse_args()

    out = {}
    for i, term in enumerate(args.terms):
        if i:
            time.sleep(PAUSE_BETWEEN)
        try:
            out[term] = fetch_term(term, args.geo, args.timeframe, log=lambda m: print(m, file=sys.stderr))
        except Exception as err:
            out[term] = {"error": str(err)[:300]}
    json.dump(out, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
