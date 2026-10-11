---
name: x-fxembed
description: Read X/Twitter data (posts, threads, replies, profiles, media, followers, search, trends) through the free FxEmbed/FxTwitter JSON API, and build fixed embed links (fxtwitter.com, fixupx.com, direct media, translate, Telegram Instant View) for Discord and Telegram. Use when the user gives an x.com or twitter.com link, asks what a post says, wants a thread unrolled, wants the images or videos from a post, a profile's recent posts, an RSS feed of an account, or a link that embeds properly in Discord or Telegram. Read-only, no login, no API key.
---

# X / Twitter via FxEmbed

FxEmbed (github.com/FxEmbed/FxEmbed, docs.fxembed.com) exposes X data as public JSON. Prefer it over scraping x.com, which needs login and blocks bots.

- Base URL: `https://api.fxtwitter.com`, versioned under `/2/`
- No auth. Limit: 1000 requests/min per IP.
- Every response has a `code` field mirroring the HTTP status. Check it, even on HTTP 200.
- Read-only. It cannot post, like, DM, or see protected or logged-in-only content.

## Quick use

Run the helper (Python 3 stdlib, handles URL parsing and retries):

```bash
S=scripts/fx.py   # path relative to this skill
python3 -I $S status https://x.com/jack/status/20      # one post
python3 -I $S thread 20                                # post plus its thread
python3 -I $S conversation 20 --ranking recency        # thread plus replies
python3 -I $S links https://x.com/user/status/123      # direct media URLs only
python3 -I $S profile @jack                            # add --about for country/rename info
python3 -I $S statuses id:12 --count 20                # recent posts (--replies, --since <unix>)
python3 -I $S media jack | followers | following | articles
python3 -I $S reposts 20 | quotes 20
python3 -I $S search "from:jack cloudflare" --feed top # latest | top | media
python3 -I $S search-users "jack" ; typeahead "clau" ; trends --count 10
```

Paginate by passing the previous response's `cursor.bottom` as `--cursor`. Add `--lang es` to translate. Add `--raw` for compact JSON.

Or call it directly: `curl -s https://api.fxtwitter.com/2/status/<id>`. Endpoints, parameters, and field names are in `references/api.md`.

## Rules that matter

1. **Post id is a numeric snowflake.** From a URL take the digits after `/status/`. Strip `?s=`, `&t=` tracking params.
2. **Handles are flaky, ids are not.** `/2/profile/{handle}...`, `/2/search` and list endpoints sometimes return a false `404` that passes on retry (observed live: same call 404, 200, 200). The helper retries 3 times. If it still 404s, switch the handle to `id:<rest_id>` (get the id from any post's `author.id`). Do not tell the user an account does not exist after one 404.
3. **Search is best-effort.** It failed far more often than other endpoints in testing. Report that honestly instead of guessing results. `/2/search/users` appears in the live OpenAPI but not in the repo's spec copy and was unverified, so confirm before relying on it.
4. **Empty is not always an error.** `/2/trends` can return 200 with an empty list. `/2/profile/{h}/statuses?since=<ts>` without `cursor` returns 204 (no body) when nothing is newer.
5. **Quote and reply context live in the object.** Use `quote` (nested post), `replying_to`, `reposted_by`, `poll`, `article`, `community_note`, `translation`. Use `raw_text` plus `facets` if you need exact entity offsets.
6. **Media URLs:** use `media.all[]` (photos, videos, gifs together). For GIFs the playable file is `transcode_url` (mp4). Videos have a `formats` array of qualities. `media.external` is an embedded third-party video.
7. **Counts are snapshots.** `views` can be null. Say "as of now" when quoting metrics.
8. **Privacy and etiquette.** Public data only. Do not bulk-crawl followers or timelines for profiling people. Stay under the rate limit. For heavy use, self-host (docs.fxembed.com/deployment).
9. **Not affiliated with X Corp.** The service is community run and can break when X changes upstream. If everything fails, check `https://status.fxtwitter.com/` and say so.

## Embed links (for pasting into Discord or Telegram)

Change only the domain. Never use these for API calls.

| Goal | Rewrite |
|---|---|
| `twitter.com` link | `fxtwitter.com` |
| `x.com` link | `fixupx.com` |
| Discord `s/e/p` trick | `twittpr.com` |
| Direct image or video file | `d.` prefix, or append `.mp4` / `.jpg` |
| Specific media in a post | append `/photo/3` or `/video/2` (combine with `d.`) |
| Translate the post | append `/en`, `/es`, ... (ISO 639-1) |
| Merge images into one | `m.` prefix |
| Media and author only | `g.` prefix |
| Text only | `t.` prefix |
| Telegram Instant View (thread reader) | `i.` prefix |
| Legacy Discord style | `o.` prefix |

Example: `https://x.com/u/status/1` becomes `https://d.fixupx.com/u/status/1/photo/2`.

Embeds only render for bot User-Agents (Discordbot, TelegramBot). In a browser the link redirects to x.com, which is expected.

## RSS / Atom for an account

`https://fxtwitter.com/{handle}/feed.xml` (RSS) or `feed.atom.xml`. Media-only: `media.xml` / `media.atom.xml`. Query: `count` (1 to 100, default 90), `with_replies`, `safe`, `lang`.

## Bluesky

Same project, sibling API: `https://api.fxbsky.app/2/...` and links via `fxbsky.app` (prefix `fx` to `bsky.app`). Spec: `https://api.fxbsky.app/2/openapi.json`. Not covered by the helper.

## When it does not fit

Need to post, like, DM, read protected accounts, or guaranteed uptime? Use the official X API (paid, needs keys) and tell the user this skill cannot do it.
