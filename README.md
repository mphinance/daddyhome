# DaddyHome

> TraderDaddy Pro **on your wall and in your smart home** — a TRMNL e-ink plugin
> and a Home Assistant integration.

**Status:** 🚧 Spec only — not built yet. This README is the build brief.

Part of the [TraderDaddy Pro](https://traderdaddy.pro) open-source family, alongside
[DaddyBoard](https://github.com/mphinance/daddyboard). Depends on
[traderdaddy-sdk](https://github.com/mphinance/traderdaddy-sdk) (TS) and the
Python mirror `traderdaddy`.

---

## Why this exists

DaddyBoard already proved the hardware-hacker overlap. DaddyHome rides two
existing open-source communities with their own distribution:

- **TRMNL** — the open-source e-ink dashboard device with a plugin marketplace.
- **Home Assistant** — huge open-source smart-home community; integrations are
  discoverable via HACS.

Both put TraderDaddy Pro in front of tinkerers who love self-hosting appliances.

## What it does

**TRMNL plugin** — a private plugin that renders a glanceable e-ink screen:
market vitals, put/call, gamma bias, top flow print. E-ink is low-refresh, so
poll on a slow market-hours cadence.

**Home Assistant integration** — exposes TraderDaddy Pro reads as HA **sensors**
(`sensor.td_put_call_ratio`, `sensor.td_market_sentiment`, `sensor.td_top_flow`,
`sensor.td_iv_rank`). Users then build their own automations/dashboards — e.g.
flash a light when a big print hits, or show flow on a wall tablet / e-ink panel.

## Architecture

- **TRMNL:** either their hosted "private plugin" (a polling URL that returns
  markup/JSON) or a small self-hosted push service. Use the **TS SDK** if it's a
  Node service.
- **Home Assistant:** a custom component (Python) — this is what needs the
  **Python `traderdaddy` SDK**. Config flow for the `td_live_` key; a
  `DataUpdateCoordinator` polling on a market-hours cadence; sensors mapped from
  tool responses.

## MCP tools used

`get_market_stats`, `get_put_call_ratios`, `get_gex_overview`, `get_iv_rank`,
`get_unusual_activity`, `get_sector_flow`.

## Key-safety model

Self-host/personal: the user supplies their own `td_live_` key — in TRMNL's
plugin settings or HA's config flow. Slow polling is naturally rate-limit-friendly.

## Build milestones

1. **Prereq:** Python `traderdaddy` SDK exists (see traderdaddy-sdk milestone 7).
2. HA custom component: config flow + coordinator + 4–5 sensors (demo data first).
3. Publish via HACS (custom repo); document installation.
4. TRMNL plugin: pick hosted-private vs self-host push; render the e-ink layout
   (reuse DaddyBoard's panel data shapes).
5. Photos/screenshots of both on real hardware for the listings.

## Picking this up in a new session

Prereq: the **Python** SDK (`traderdaddy` on PyPI). If it doesn't exist yet, do
that first (mirror `@traderdaddy/sdk`). HA integration is the higher-value half
(bigger community, HACS discovery) — start there; TRMNL can follow on the TS SDK.
