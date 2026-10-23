"""Optional: read Google Trends through the Apify Actor smallhourstools/google-trends-polite.

Usage:
    export APIFY_TOKEN=...        # from your own Apify account, Settings > API & Integrations
    python3 apify_trends.py "cold brew" --geo US --timeframe "today 12-m"

The Actor waits and retries on Google's 429 itself, so a run takes about a minute per term.
This script starts the run, polls until it ends and prints the dataset items. Standard library only.
"""
import argparse
import json
import os
import sys
import time
import urllib.request

API = "https://api.apify.com/v2"
ACTOR = "smallhourstools~google-trends-polite"


def call(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{API}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def run_actor(terms, geo="", time_range="today 12-m", token=None, max_wait=3600):
    token = token or os.environ.get("APIFY_TOKEN")
    if not token:
        raise SystemExit("Set APIFY_TOKEN in your environment. Do not paste the token into the code.")
    run = call("POST", f"/acts/{ACTOR}/runs", token, {
        "searchTerms": terms, "geo": geo, "timeRange": time_range,
        "includeRegions": False, "includeRelated": False,
    })["data"]
    deadline = time.time() + max_wait
    while run["status"] in ("READY", "RUNNING"):
        if time.time() > deadline:
            raise SystemExit(f"Run {run['id']} is still going after {max_wait}s. Check it in the Apify console.")
        time.sleep(15)
        run = call("GET", f"/actor-runs/{run['id']}", token)["data"]
    if run["status"] != "SUCCEEDED":
        raise SystemExit(f"Run ended with status {run['status']}.")
    return call("GET", f"/datasets/{run['defaultDatasetId']}/items?clean=true", token)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("terms", nargs="+")
    parser.add_argument("--geo", default="")
    parser.add_argument("--timeframe", default="today 12-m")
    args = parser.parse_args()
    items = run_actor(args.terms, args.geo, args.timeframe)
    json.dump(items, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
