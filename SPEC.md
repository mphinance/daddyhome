# SPEC — daddyhome full-SDK expansion (2026-07-16)

Build-mode spec, executed from `FINDINGS.md`. Goal: cover all 24 SDK tools,
generalize the automation surface, add HA-native calendar entities, ship a
custom Lovelace card (Playwright-screenshotted for the README), and document
a Grafana/InfluxDB long-term-trend recipe.

## Ground truth already gathered

- `traderdaddy-sdk/traderdaddy-sdk/python/traderdaddy/client.py` — 24 typed
  methods, one per MCP tool.
- `traderdaddy-sdk/traderdaddy-sdk/python/traderdaddy/types.py` — exact field
  shapes for every response (TypedDicts).
- `traderdaddy-sdk/traderdaddy-sdk/python/traderdaddy/mock/fixtures.py` —
  realistic mock values for every tool (keyless demo path).
- `traderdaddy-sdk/traderdaddy-sdk/python/traderdaddy/cache.py` `DEFAULT_TTLS`
  — per-tool freshness windows, used here as the cadence-tier assignment.

## Architecture change: two coordinators, one shared client

`coordinator.py` (**fast**, existing market-hours cadence 2min open / 15min
closed) keeps the original 6 tools and gains `market_health`,
`institutional_activity`, `conviction()` (market-wide), `bounce_signals()` —
all market-wide, cheap, high-signal.

New `coordinator_slow.py` (**slow**, 10min open / 30min closed) owns
everything ticker-scoped-to-the-configured-symbol plus the heavier/rotating
tools: `run_screener` (rotates one screener per cycle, mirrors DaddyBoard),
`strategy_ideas`, `edge_xray`, `gex_ticker`, `apex_levels`, `bounce_score`,
`conviction(symbol)`, `long_term_quality`, `politician_trades`,
`politician_trades_by_ticker`, `dividend_calendar`, `economic_calendar`,
`earnings_flow`, `ipo_scanner` (rotates view per cycle).

That's 10 fast + 14 slow = **all 24 tools polled**. `hedge_analysis` needs
call-time args (`shares`, `basis?`) so it's NOT polled — it's registered as
an HA **service with response data** (`traderdaddy.hedge_analysis`).

Both coordinators share **one** `TraderDaddy` client instance, created once
in `__init__.py` and injected into both — keeps CLAUDE.md's "one SDK
instantiation" spirit while allowing two poll cadences.

`hass.data[DOMAIN][entry.entry_id]` becomes a small dict
`{"fast": <coordinator>, "slow": <coordinator>, "client": <TraderDaddy>}`
instead of a bare coordinator — every platform file updates its lookup.

**Scope call:** multi-ticker (watching more than one symbol) is NOT done in
this pass — it's a real architecture project (HA config subentries, per-
symbol devices) flagged as future work in `FINDINGS.md`. This build keeps
the existing single-`symbol` config and hangs every new ticker-scoped tool
off that one symbol, same pattern as the existing `iv_rank`/`put_call_ratios`.

## New entities

- **sensor.py**: ~16 new descriptions across fast/slow tiers (market_health,
  institutional_activity, conviction ×2, bounce_signals, screener rotation,
  strategy_ideas, edge_xray, gex_ticker, apex_levels, bounce_score,
  long_term_quality, politician_trades, politician_trades_by_ticker,
  dividend_calendar, ipo_scanner rotation).
- **binary_sensor.py**: `td_gamma_flip`, `td_elevated_risk` (market_health
  composite over threshold), `td_bounce_signal`, `td_high_conviction` —
  alongside the existing `td_legendary_print`.
- **event.py** (new platform): `event.td_new_print` (any tier, generalizes
  the binary sensor), `event.td_new_politician_trade`,
  `event.td_new_ipo_listing`, `event.td_earnings_approaching`. Each tracks
  "seen" ids internally so only genuinely new items fire.
- **calendar.py** (new platform): three HA `CalendarEntity` implementations
  over `economic_calendar`, `earnings_flow`, `dividend_calendar` — shows up
  natively in HA's calendar dashboard/automations.
- **services.yaml + __init__.py service registration**:
  `traderdaddy.hedge_analysis(symbol, shares, basis?, atr?)` → response data.

## Dashboard / "Grafana-like" deliverables

- `www/traderdaddy-vitals-card.js` — vanilla-JS custom Lovelace card (no
  build step, same trick DaddyBoard already proved), dark glassmorphism,
  sentiment gauge + top flow + gamma bias. Auto-served from HA's `/local/`.
- `www/preview.html` — standalone harness loading the card with mock data
  matching the real sensor attribute shapes, for local viewing AND for the
  Playwright screenshot pipeline (no running HA instance required).
- `docs/screenshot-card.png` — Playwright-captured screenshot of the card,
  embedded in `README.md`.
- `docs/GRAFANA.md` + `docs/grafana-dashboard.json` — InfluxDB export recipe
  + an importable Grafana dashboard for long-term trend (HA's recorder only
  keeps ~10 days; this is the actual Grafana value-add over native HA history).

## Out of scope (flagged, not built)

- Multi-ticker / config subentries (see above).
- TRMNL e-ink plugin — unrelated, tracked separately in README.
- Publishing the custom card as a HACS "plugin" repo type — ships as a
  bundled `www/` asset with manual resource-add instructions in the README.

## Acceptance

- Every `.py` file passes `python3 -m py_compile`.
- `strings.json`/`translations/en.json`/`manifest.json`/`services.yaml`/
  `docs/grafana-dashboard.json` are valid JSON/YAML.
- All new sensors/binary_sensors/events/calendars have a `value_fn`/property
  reading only from the coordinator's cached dict — no direct SDK calls
  outside the two coordinators (CLAUDE.md's core rule, now for two coordinators).
- `www/preview.html` renders the card with zero console errors under
  Playwright and produces `docs/screenshot-card.png`.
- README documents every entity (sensor/binary_sensor/event/calendar) and the
  new service, with the screenshot embedded.
- Nothing outside `custom_components/traderdaddy/`, `www/`, `docs/`,
  `README.md`, `CLAUDE.md` is modified.
