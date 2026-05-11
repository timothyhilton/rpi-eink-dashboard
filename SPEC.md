# RPi Eink Dashboard — Spec

## Goal
Compact at-a-glance dashboard on Waveshare epd3in7 (280×480, 4-gray). Refresh once per N minutes via cron. Show today's weather, calendar, email — nothing else.

## Hardware / constraints
- Waveshare epd3in7, 4-gray (`epd.display_4Gray`).
- Portrait 280×480 (after `rotate(270, expand=True)` on source).
- Slow partial refreshes — design for static-ish layout, no animation.
- Pi runs headless; script invoked by cron/systemd timer.

## Data sources
1. **Weather** — weatherapi.com `forecast.json?days=1` (gives today high/low + chance of rain). Location: Brisbane. Key already in repo (rotate before public push).
2. **Calendar** — Google Calendar API. Read-only OAuth, primary calendar. Today's events only (00:00 → 23:59 local).
3. **Email** — Gmail API. Read-only OAuth. Count unread in INBOX, list top 3 sender+subject (truncated).

OAuth tokens cached on disk (`~/.config/rpi-dashboard/`). Refresh handled silently.

## Layout (280 wide × 480 tall)

```
+--------------------------------+
| HEADER  date  ·  HH:MM updated | 40px
+--------------------------------+
| WEATHER                        |
|  icon  28°/19°  Rain 70%       | 100px
|  "Showers, windy"              |
+--------------------------------+
| NEXT EVENT  (prominent)        |
|  13:30  in 2h                  | 90px
|  Dentist — Spring Hill         |
+--------------------------------+
| CALENDAR — today               |
|  09:00  Standup                | 110px
|  16:00  1:1 with X             |
|  (+2 more)                     |
+--------------------------------+
| LATEST EMAIL  (prominent)      |
|  Alice Chen · 9:42am           | 70px
|  Q3 review draft ready         |
+--------------------------------+
| EMAIL — 7 unread               |
|  Bob    · Re: invoice          | 70px
|  GitHub · PR #482 review req   |
+--------------------------------+
```

Prominent rows = larger font, bold, taller row. Section heights tunable. Empty section collapses; others expand.

### Prominent-row selection
- **Next event**: soonest event with `start >= now` today. If none remaining today, hide section. All-day events not eligible (shown only in list).
- **Latest email**: most recent unread INBOX message. If zero unread, hide section.
- The prominent item is **excluded** from the list section below it to avoid duplication.

## Behaviour rules
- **Stale data**: if a fetch fails, render last-known value with a `!` marker next to the section header. Never blank a section on transient failure.
- **Truncation**: ellipsis on overflow per line, never wrap calendar/email rows.
- **All-day events**: shown without time, sorted before timed events.
- **Rain logic**: show `Rain X%` only when `daily_chance_of_rain >= 30`, else show condition text.
- **Email priority**: optional — flag senders matching configured regex (`important_senders.txt`) with `★`.
- **Quiet hours**: skip refresh 23:00–06:00 to save panel wear.

## Code structure
```
main.py              # orchestrator: fetch -> compose -> render
sources/
  weather.py         # WeatherAPI client, returns dataclass
  calendar.py        # Google Calendar client
  email.py           # Gmail client
render/
  layout.py          # section layout + bbox math
  widgets.py         # draw_weather, draw_calendar, draw_email, draw_header
  fonts.py           # font registry
config.py            # location, refresh interval, paths, secrets loader
cache.py             # last-known-good JSON per source
```

`TEST_MODE` writes PNG to `images/out/out.png` (current behaviour). Production path drives epd.

## Config
`config.toml`:
```toml
location = "Brisbane"
refresh_minutes = 30
quiet_hours = [23, 6]

[weather]
api_key_env = "WEATHERAPI_KEY"

[google]
credentials_path = "~/.config/rpi-dashboard/credentials.json"
token_path = "~/.config/rpi-dashboard/token.json"
calendar_id = "primary"

[email]
max_rows = 3
important_senders_path = "important_senders.txt"
```

Secrets via env / file, never hardcoded.

## Out of scope (v1)
- Multiple calendars, multi-day forecast, news/RSS, todos, transit, sensors, web UI, OTA config.

## Open questions
- Font for icons — emoji renders poorly on 4-gray. Use a weather glyph font (e.g. Weather Icons TTF).
- Auth flow on headless Pi — first-run on dev machine, copy `token.json` over.
- Time zone handling — pin to `Australia/Brisbane` explicitly.
