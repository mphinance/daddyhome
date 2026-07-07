# DaddyHome

> TraderDaddy Pro **on your wall and in your smart home** — a TRMNL e-ink plugin
> and a Home Assistant integration.

**Status:** ✅ Home Assistant integration built (HACS-installable, keyless demo
mode; add your `td_live_` key to go live). 🚧 TRMNL e-ink plugin still to come.

Part of the [TraderDaddy Pro](https://traderdaddy.pro) open-source family, alongside
[DaddyBoard](https://github.com/mphinance/daddyboard). Depends on
[traderdaddy-sdk](https://github.com/mphinance/traderdaddy-sdk) (TS) and the
Python mirror [`traderdaddy`](https://pypi.org/project/traderdaddy/).

**Customizing it?** Grab a prompt from [`PROMPTS.md`](PROMPTS.md) and paste it into
Claude Code / Cursor. Agents working in this repo should read [`CLAUDE.md`](CLAUDE.md).

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

## Status & what's next

**Done:**

1. ✅ Python `traderdaddy` SDK (the prereq) — shipped on PyPI.
2. ✅ HA custom component: config flow + market-hours coordinator + sensors and
   binary sensors, all demo-first (`mock=True` with no key).
3. ✅ HACS metadata (`hacs.json`) for custom-repo install.

**Still to come:**

4. 🚧 TRMNL plugin — pick hosted-private vs self-host push; render the e-ink
   layout on the **TS** SDK (reuse DaddyBoard's panel data shapes).
5. 🚧 Photos/screenshots on real hardware for the listings.

Adding a sensor, tuning the cadence, or starting the TRMNL plugin? Grab a prompt
from [`PROMPTS.md`](PROMPTS.md); [`CLAUDE.md`](CLAUDE.md) has the conventions.
