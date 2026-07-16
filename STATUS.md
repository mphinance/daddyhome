# STATUS — full-SDK expansion (2026-07-16)

Build-mode pass executed against `SPEC.md`/`feature_list.json`, seeded from
`FINDINGS.md`'s Recon-mode ideation. All 24 `traderdaddy` SDK tools are now
polled and exposed; ships a custom Lovelace card and a Grafana recipe.

## Shipped

- **Two-coordinator architecture** — `coordinator.py` (fast, 10 tools,
  market-hours cadence) + new `coordinator_slow.py` (slow, 14 tools, tracked
  symbol + rotating screeners/IPO scanner), sharing one `TraderDaddy` client
  instantiated once in `__init__.py`.
- **23 sensors** (11 fast + 12 slow), **5 binary sensors** (1 original + 4
  new: gamma_flip, elevated_risk, bounce_signal, high_conviction), **4 event
  entities** (new platform — dedup'd "new item" triggers), **3 calendar
  entities** (new platform — economic/earnings/dividend, native
  `CalendarEntity`).
- **`hedge_analysis` HA service** with response data (`SupportsResponse.ONLY`)
  — the one tool that needs call-time args, so it isn't polled.
- **Custom Lovelace card** (`www/traderdaddy-vitals-card.js`) — vanilla JS, no
  build step, dark glassmorphism matching DaddyBoard's design language.
  `www/preview.html` is a standalone mock-data harness.
- **Playwright screenshot** captured from the preview harness into
  `docs/screenshot-card.png`, embedded in the README.
- **Grafana/InfluxDB recipe** (`docs/GRAFANA.md` + `docs/grafana-dashboard.json`)
  — docs-only, for long-term trend beyond HA's ~10-day recorder retention.
- **`strings.json`/`translations/en.json`** updated with names for every new
  entity.
- **README** fully rewritten: entity tables for all four platforms, service
  docs, screenshot, architecture section.
- **CLAUDE.md** updated to describe the two-coordinator/shared-client
  architecture and the expanded repo map.

## Bug fix along the way

The original `market_sentiment`/`total_flow_premium` sensors read camelCase
fields (`overallSentiment`, `totalFlowPremium`, etc.) that don't exist on the
real `MarketStats` payload — it's snake_case per `types.py`'s explicit code
comment. Fixed while rewriting `sensor.py`: `market_sentiment` now reads
`spy_sentiment` + related snake_case fields, `total_flow_premium` reads
`unusual_activity.aggregates.totalPremium`.

## Verified

- `python3 -m py_compile` — all `.py` files in `custom_components/traderdaddy` pass.
- `strings.json`, `translations/en.json`, `manifest.json`,
  `docs/grafana-dashboard.json` — valid JSON. `services.yaml` — valid YAML.
- `grep -rn "self.client\."` outside `coordinator.py`/`coordinator_slow.py` —
  zero matches. No entity calls the SDK directly.
- `www/preview.html` renders the card correctly under Playwright — screenshot
  captured, all six tiles populated, legendary badge renders.
- `git status --short` confined to `custom_components/traderdaddy/`, `www/`,
  `docs/`, `README.md`, `CLAUDE.md`, `SPEC.md`, `feature_list.json`,
  `FINDINGS.md`, `STATUS.md`.

## Out of scope (flagged, not built — see `FINDINGS.md`/`SPEC.md`)

- Multi-ticker / config subentries (watching more than one symbol).
- TRMNL e-ink plugin — unrelated, tracked separately.
- Publishing the custom card as a HACS "plugin" repo type — ships as a
  bundled `www/` asset with manual resource-add instructions.

## Fixed since the last pass

- **Entity-id mismatch resolved.** `entity.py` now sets
  `_attr_suggested_object_id = f"td_{key}"` on every entity, so HA's
  auto-generated entity ids are actually `sensor.td_market_sentiment` etc. —
  matching what the README, CLAUDE.md, and the custom card's defaults always
  assumed. (Only applies on first creation; a user who already renamed an
  entity keeps their own id.) `www/traderdaddy-vitals-card.js`'s
  `DEFAULT_ENTITIES` and `www/preview.html`'s mock data updated to match.
