#!/usr/bin/env python3
"""Read-only CLI for the FxTwitter API v2 (https://api.fxtwitter.com). Stdlib only.

Usage: fx.py <command> <target> [--count N] [--cursor C] [--lang xx] [--feed latest|top|media]
              [--replies] [--about] [--ranking likes|recency] [--since TS] [--raw]
Commands: status thread conversation reposts quotes profile about statuses media articles
          followers following search search-users typeahead trends links
Targets: tweet URL or id, handle (with or without @), or id:<rest_id>; query text for search.
"""
import argparse, json, re, sys, time, urllib.parse, urllib.request, urllib.error

BASE = "https://api.fxtwitter.com"
UA = "x-fxembed-skill/1.0"
# Endpoints that return 404 with empty results when upstream flakes (seen live).
FLAKY_EMPTY = ("/statuses", "/media", "/followers", "/following", "/2/search", "/articles")

def tweet_id(t):
    m = re.search(r"status(?:es)?/(\d+)", t) or re.fullmatch(r"(\d+)", t.strip())
    if not m:
        sys.exit(f"error: cannot find a tweet id in {t!r}")
    return m.group(1)

def handle(t):
    t = t.strip()
    m = re.match(r"https?://(?:www\.|mobile\.)?(?:x|twitter|fxtwitter|fixupx)\.com/([^/?#]+)", t)
    t = m.group(1) if m else t
    return t if t.lower().startswith("id:") else t.lstrip("@")

def get(path, params, retries=3):
    q = {k: v for k, v in params.items() if v not in (None, "", False)}
    url = BASE + path + ("?" + urllib.parse.urlencode(q) if q else "")
    last = None
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                body = r.read()
                return json.loads(body) if body else {"code": r.status}
        except urllib.error.HTTPError as e:
            raw = e.read()
            try: last = json.loads(raw)
            except Exception: last = {"code": e.code, "message": raw[:200].decode("utf8", "replace")}
            retry = e.code >= 500 or e.code == 429 or (e.code == 404 and (path.startswith("/2/profile/") and path.count("/") == 3 or path.endswith(FLAKY_EMPTY) or "/2/search" in path))
            if not retry: return last
        except urllib.error.URLError as e:
            last = {"code": 0, "message": str(e.reason)}
        if i < retries: time.sleep(1.5 * (i + 1))
    last["note"] = f"still failing after {retries + 1} attempts; a persistent 404 may be real, or try id:<rest_id>"
    return last

def media_links(d):
    s = d.get("status") or d.get("tweet") or {}
    out = []
    for m in (s.get("media") or {}).get("all") or []:
        out.append({"type": m.get("type"), "url": m.get("url"), "w": m.get("width"), "h": m.get("height"),
                    "alt": m.get("altText"), "gif_mp4": m.get("transcode_url") if m.get("type") == "gif" else None})
    return out

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd"); p.add_argument("target", nargs="?", default="")
    p.add_argument("--count", type=int); p.add_argument("--cursor"); p.add_argument("--lang")
    p.add_argument("--feed"); p.add_argument("--ranking"); p.add_argument("--since")
    p.add_argument("--replies", action="store_true"); p.add_argument("--about", action="store_true")
    p.add_argument("--raw", action="store_true", help="print full JSON (default trims nothing; for 'media' prints links only)")
    a = p.parse_args()
    c, t = a.cmd, a.target
    pg = {"count": a.count, "cursor": a.cursor}
    if c in ("status", "thread"):
        d = get(f"/2/{c}/{tweet_id(t)}", {"lang": a.lang, "about_account": a.about})
    elif c == "conversation":
        d = get(f"/2/conversation/{tweet_id(t)}", {"ranking_mode": a.ranking, "cursor": a.cursor, "lang": a.lang, "about_account": a.about})
    elif c in ("reposts", "quotes"):
        d = get(f"/2/status/{tweet_id(t)}/{c}", {**pg, "lang": a.lang if c == "quotes" else None})
    elif c == "profile":
        d = get(f"/2/profile/{handle(t)}", {"about_account": a.about})
    elif c == "about":
        d = get(f"/2/profile/{handle(t)}/about", {})
    elif c in ("statuses", "media", "articles"):
        d = get(f"/2/profile/{handle(t)}/{c}", {**pg, "lang": a.lang, **({"with_replies": a.replies, "since": a.since} if c == "statuses" else {})})
    elif c in ("followers", "following"):
        d = get(f"/2/profile/{handle(t)}/{c}", pg)
    elif c == "search":
        d = get("/2/search", {"q": t, "feed": a.feed, **pg, "lang": a.lang})
    elif c == "search-users":
        d = get("/2/search/users", {"q": t, **pg, "lang": a.lang})
    elif c == "typeahead":
        d = get("/2/typeahead", {"q": t})
    elif c == "trends":
        d = get("/2/trends", {"count": a.count})
    elif c == "links":  # media links of a tweet, no raw JSON
        d = {"media": media_links(get(f"/2/status/{tweet_id(t)}", {}))}
    else:
        sys.exit(f"error: unknown command {c!r}")
    json.dump(d, sys.stdout, ensure_ascii=False, indent=None if a.raw else 2); print()
    sys.exit(0 if d.get("code", 200) < 400 else 1)

if __name__ == "__main__":
    main()
