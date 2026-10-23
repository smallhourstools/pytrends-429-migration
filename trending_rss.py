"""Read what is trending today from the Google Trends RSS feed. No pytrends, no account, standard library only.

Usage:
    python3 trending_rss.py --geo US
"""
import argparse
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET

URL = "https://trends.google.com/trending/rss?geo={geo}"
USER_AGENT = "trends-migration-example (+https://github.com/smallhourstools/pytrends-429-migration)"


def local(tag):
    return tag.rsplit("}", 1)[-1]


def fetch_trending(geo="US"):
    request = urllib.request.Request(URL.format(geo=geo), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())
    items = []
    for item in root.iter("item"):
        row = {}
        for child in item:
            name = local(child.tag)
            if name in ("title", "pubDate", "approx_traffic"):
                row[name] = (child.text or "").strip()
        if "title" in row:
            items.append({
                "title": row["title"],
                "approxTraffic": row.get("approx_traffic", ""),
                "published": row.get("pubDate", ""),
            })
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--geo", default="US")
    args = parser.parse_args()
    items = fetch_trending(args.geo)
    json.dump(items, sys.stdout, indent=2)
    print()
    print(f"{len(items)} items", file=sys.stderr)


if __name__ == "__main__":
    main()
