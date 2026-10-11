# FxTwitter API v2 reference

Source of truth: `https://api.fxtwitter.com/2/openapi.json` (machine-readable, always current). Docs: https://docs.fxembed.com/api/introduction. Verified against the live spec on 2026-10-11.

## Endpoints (all GET, base `https://api.fxtwitter.com`)

| Path | Purpose | Params |
|---|---|---|
| `/2/status/{id}` | One post | `lang`, `about_account` |
| `/2/thread/{id}` | Post plus unrolled thread | `lang`, `about_account` |
| `/2/conversation/{id}` | Thread to root plus replies | `ranking_mode` (`likes` default, `recency`), `cursor`, `lang`, `about_account` |
| `/2/status/{id}/reposts` | Users who reposted | `count` (1-100, 20), `cursor` |
| `/2/status/{id}/quotes` | Posts quoting it (Latest tab) | `count`, `cursor`, `lang` |
| `/2/profile/{handle}` | User profile | `about_account` |
| `/2/profile/{handle}/about` | Country, rename history | none |
| `/2/profile/{handle}/statuses` | Timeline | `count`, `cursor`, `since` (unix s or ms), `with_replies`, `groupthreads`, `lang` |
| `/2/profile/{handle}/media` | Posts with media | `count`, `cursor`, `lang` |
| `/2/profile/{handle}/articles` | Long-form articles | `count`, `cursor`, `lang` |
| `/2/profile/{handle}/followers`, `/following` | Relationship lists | `count`, `cursor` |
| `/2/search` | Search posts | `q` (required), `feed` (`latest` default, `top`, `media`), `count` (1-100, 30), `cursor`, `lang` |
| `/2/search/users` | People search (live spec only, unverified) | `q`, `count`, `cursor`, `lang` |
| `/2/typeahead` | Autocomplete | `q`, `result_type` (`events,users,topics`), `src` |
| `/2/trends` | Trending | `type=trending`, `count` (1-50, 20) |

`{handle}` is a username without `@`, or `id:<rest_id>` (case-insensitive prefix). Legacy v1 `/{handle}/status/{id}` still works but returns the older `tweet` key and lacks newer fields.

## Response envelopes

- Single post: `{"code":200,"message":"OK","status":{...}}`. `/thread` and `/conversation` add `thread` (the chain), `author`; `/conversation` also adds `replies` and `cursor`.
- Lists: `{"code":200,"results":[...],"cursor":{"top":..,"bottom":..}}`. Next page = `cursor.bottom`.
- Profile: `{"code":200,"user":{...}}`
- Errors: `{"code":400|404|500,"message":"..."}`. A bad id gives `400 id: tweet ID must be a numeric snowflake`. Failed list calls give `404` with `results: []`.
- Status codes: 200, 204 (`since` with nothing newer), 400, 401 ("Private or unavailable post"), 404, 500.

## Post object (`APITwitterStatus`)

`type, id, url, text, raw_text{text,display_text_range,facets}, created_at, created_timestamp, author(APIUser), likes, reposts, quotes, replies, bookmarks, views, lang, translation, possibly_sensitive, source, is_note_tweet, replying_to, reposted_by, quote (nested post), poll{choices[{label,count,percentage}],total_votes,ends_at}, media{all,photos,videos,external,mosaic,broadcast}, article, community, community_note, card, embed_card, provider`

Photo: `id, type(photo|gif), url, width, height, altText, transcode_url`. Video: `id, type(video|gif), url, width, height, thumbnail_url, transcode_url, duration, filesize, formats[]`.

## User object (`APIUser`)

`id, screen_name, name, description, raw_description, location, url, avatar_url, banner_url, protected, followers, following, statuses, media_count, likes, joined, website, birthday, verification, about_account{based_in,location_accurate,source,username_changes}`

## Tombstones

A post that cannot be shown can come back as `APIStatusTombstone` (`type, provider, reason, message, id, url, author`) instead of a post. Check `status.type` and read `reason` before using other fields.

## Observed behavior (2026-10-11, one IP)

- `/2/status/{id}`, `/2/profile/id:{n}`, `/2/profile/id:{n}/statuses`, `/2/typeahead`, `/2/conversation/{id}` returned 200 consistently.
- `/2/profile/{handle}` and `/2/profile/{handle}/about` returned an occasional false 404.
- `/2/search` returned 404 with empty results most of the time. Do not treat as proof of no matches.
- `/2/trends` returned 200 but sometimes an empty `trends` list.

## Search `feed` param (tested 2026-10-11)

Accepted values: `latest`, `top`, `media`. Any other value returns `400 feed: Invalid option: expected one of "latest"|"top"|"media"`. In testing, `latest` returned results on 1 of 2 tries, and `top` and `media` returned the empty 404 on every try, so the param is valid but search is unreliable.

## RSS / Atom feeds (tested 2026-10-11)

See `SKILL.md`. 200 for `feed.xml`, `feed.atom.xml`, `media.xml`, `media.atom.xml` on X and `feed.xml`, `feed.atom.xml` on Bluesky, after retrying transient 404s. Not tested: Bluesky `media*.xml`, `withReplies`/`language` aliases, enclosure contents.
