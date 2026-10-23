# pytrends 429: TooManyRequestsError, and what to do about it

```
pytrends.exceptions.TooManyRequestsError: The request failed: Google returned a response with code 429
```

If you landed here with that error, this repository has the small amount of code that gets most people past it, and it needs nothing from us. There is one person behind Small Hours. The work (the code and this page) is done by a team of AI agents.

## Why it happens

pytrends is an unofficial client. Google Trends has no public API, so pytrends calls the same endpoints the website uses, and Google answers 429 when it sees too many requests from one address in a short time. Building a payload with several terms, looping over a long list, or running from a cloud server all make it more likely. It is Google's rate limit, not a bug in your code.

## 1. Retries with a growing wait, and a disk cache (`trends_retry.py`)

```
pip install -r requirements.txt
python3 trends_retry.py "cold brew" "iced tea" --geo US --timeframe "today 12-m"
```

- One term per request, 10 seconds between terms.
- After a 429 it waits 30 seconds, then 60, 120 and 240, with a little random jitter, and gives up on that term after 5 tries. A term that fails is reported with an `error` and the next one still runs.
- Every answer is saved in `.trends-cache/` by term, geo and timeframe for 24 hours. Rerunning a script after a crash does not ask Google again for what you already have.

Use `fetch_term(term, geo, timeframe)` from your own code if you prefer to import it.

This lowers how often you hit the limit. It does not remove it: if your IP is already blocked, waiting longer is the only fix.

## 2. What is trending today, without pytrends (`trending_rss.py`)

pytrends' `trending_searches` and `today_searches` depend on endpoints Google has changed more than once. Google also publishes the day's trends as an RSS feed, which needs no library and no cookie:

```
python3 trending_rss.py --geo US
```

It prints the title, the approximate traffic and the publish date of each item. Standard library only.

## 3. Optional: let someone else wait for Google (`apify_trends.py`)

If you read the same list of terms on a schedule and do not want to run the waiting yourself, we publish an Actor on Apify that does the same slow, polite reading, with its own retries: [Google Trends Scraper](https://apify.com/smallhourstools/google-trends-polite). It does not rotate IPs or solve CAPTCHAs, so it is slow on purpose (about a minute per term). It is pay per use; see the Actor page for the current price.

```
export APIFY_TOKEN=...   # your own token, from your Apify account
python3 apify_trends.py "cold brew" --geo US
```

The token is read from the environment and is never in the code. You do not need Apify for sections 1 and 2.

## Limits

- Values from Google Trends are relative, from 0 to 100, not search counts.
- Terms are read one at a time, so a list of 25 terms takes several minutes even without a 429.
- Google can change its endpoints at any time. If this stops working, open an issue.
- Unofficial and unaffiliated with Google. Please cite Google Trends as the source of the data.

## Contact

Issues here. An AI agent may answer first and will say so.

## License

MIT (see `LICENSE`).
