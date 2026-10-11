# dawood-skills

Claude Code plugin and marketplace holding Dawood's skills.

## Install

```
/plugin marketplace add EngDawood/skills
/plugin install dawood-skills@dawood-skills
```

## Skills

| Skill | What it does |
|---|---|
| `x-fxembed` | Read X/Twitter posts, threads, profiles, media, RSS feeds via the FxEmbed API, and build fixed embed links for Discord and Telegram. Read-only, no login. |

## Adding a skill

Create `skills/<name>/SKILL.md` with `name` and `description` frontmatter. The plugin picks it up automatically. Bump `version` in both files under `.claude-plugin/`.
