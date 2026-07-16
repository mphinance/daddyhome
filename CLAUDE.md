# CLAUDE.md — agent ground-truth for DaddyHome

> Read this first. The short, factual map for working in this repo. Tool-agnostic
> — copy to `AGENTS.md` if you use Cursor/other.
>
> **Want to customize it by talking to your AI?** See [`PROMPTS.md`](PROMPTS.md).

## What this is

TraderDaddy Pro in your smart home. **Built:** a Home Assistant custom integration
(HACS-installable) that exposes market reads as HA sensors. **Planned:** a TRMNL
e-ink plugin (not built yet). Unlike the rest of the family this half is
**Python** — it rides the [`traderdaddy`](https://pypi.org/project/traderdaddy/)
PyPI SDK (the async mirror of `@traderdaddy/sdk`), pinned in `manifest.json` as
`traderdaddy>=0.1.0`.

## Repo map

| Path | What |
|---|---|
| `custom_components/traderdaddy/__init__.py` | Entry setup/unload; creates the **one** shared `TraderDaddy` client and both coordinators; registers the `hedge_analysis` service. |
| `custom_components/traderdaddy/config_flow.py` | UI config flow (initial `td_live_` key + symbol) plus the options flow (change symbol, rotate/add API key in-place). |
| `custom_components/traderdaddy/diagnostics.py` | HA "download diagnostics" support — redacted config entry + both coordinators' cached data. |
| `custom_components/traderdaddy/coordinator.py` | **Fast-tier** `DataUpdateCoordinator` — market-hours cadence, market-wide vitals + tracked-symbol core reads (10 tools). |
| `custom_components/traderdaddy/coordinator_slow.py` | **Slow-tier** `DataUpdateCoordinator` — long cadence, everything scoped to the tracked symbol plus rotating screeners/IPO scanner (14 tools). |
| `custom_components/traderdaddy/sensor.py` | Sensors — each is one `value_fn`/`attr_fn` over a coordinator's cache. `FAST_SENSORS` bind to `coordinator.py`, `SLOW_SENSORS` bind to `coordinator_slow.py`. |
| `custom_components/traderdaddy/binary_sensor.py` | Binary sensors (fast tier) — threshold on/off triggers for automations. |
| `custom_components/traderdaddy/event.py` | `event` platform — dedup'd "new item" triggers (new print, new politician trade, new IPO, earnings approaching). |
| `custom_components/traderdaddy/calendar.py` | `calendar` platform (slow tier) — economic/earnings/dividend calendars as native HA `CalendarEntity`s. |
| `custom_components/traderdaddy/services.yaml` | Schema for the `hedge_analysis` service. |
| `custom_components/traderdaddy/entity.py` | Shared base entity — works with either coordinator tier (`AnyTraderDaddyCoordinator`); sets `_attr_suggested_object_id` so entity ids are predictable (`sensor.td_*`). |
| `custom_components/traderdaddy/const.py` | `DOMAIN`, conf keys, fast/slow `SCAN_INTERVAL_*`, screener/IPO-view rotation lists, `PLATFORMS`. |
| `custom_components/traderdaddy/manifest.json` | HA manifest — `requirements: ["traderdaddy>=0.1.0"]`. |
| `custom_components/traderdaddy/strings.json` + `translations/` | Config-flow + entity-name UI strings. |
| `www/traderdaddy-vitals-card.js` + `www/preview.html` | No-build custom Lovelace card + a standalone mock-data harness for viewing/screenshotting it. |
| `docs/GRAFANA.md` + `docs/grafana-dashboard.json` | InfluxDB + Grafana long-term-trend recipe (HA's recorder only keeps ~10 days). |
| `blueprints/automation/traderdaddy/notify_on_legendary_print.yaml` | Importable automation blueprint — notify on a LEGENDARY print, no YAML/Python needed. |
| `hacs.json` | HACS metadata (custom-repo install). |

## The one rule

The SDK is instantiated **exactly once**, in `__init__.py`, and shared by both
coordinators. Each coordinator's `_async_update_data` cycle fetches its tool
set into a dict; every sensor/binary_sensor/event/calendar reads from a
coordinator's cached dict via its `value_fn`/`is_on_fn`/etc — **entities never
call the SDK directly.** Adding an entity = one description with a
`value_fn`, no new polling. This holds for two coordinators now instead of
one — check `self.client.` only appears in `coordinator.py` and
`coordinator_slow.py` before landing a change.

## How it runs

- **No key → keyless demo** (`TraderDaddy(mock=True)`) — the funnel default. With
  a key, `TraderDaddy(api_key=…, client=get_async_client(hass))` shares HA's own
  httpx client rather than spinning up its own.
- **Two poll tiers, one client:**
  - Fast (`coordinator.py`): `SCAN_INTERVAL_OPEN` = 2 min, `SCAN_INTERVAL_CLOSED`
    = 15 min. Market-wide vitals + tracked-symbol core reads — `market_stats`,
    `unusual_activity`, `gex_overview`, `iv_rank`, `sector_flow`,
    `put_call_ratios`, `market_health`, `institutional_activity`, `conviction`
    (market-wide), `bounce_signals`.
  - Slow (`coordinator_slow.py`): `SCAN_INTERVAL_SLOW_OPEN` = 10 min,
    `SCAN_INTERVAL_SLOW_CLOSED` = 30 min. Tracked-symbol + heavier/rotating
    tools — `run_screener` (rotates `SCREENER_ROTATION`, one per cycle),
    `strategy_ideas`, `edge_xray`, `gex_ticker`, `apex_levels`, `bounce_score`,
    `conviction` (symbol), `long_term_quality`, `politician_trades`,
    `politician_trades_by_ticker`, `dividend_calendar`, `economic_calendar`,
    `earnings_flow`, `ipo_scanner` (rotates `IPO_VIEW_ROTATION`).
  - Both re-tune their interval each cycle from `is_market_open()`.
- **`hedge_analysis` is a service, not polled** — it needs call-time args
  (`shares`, `basis?`). Registered in `__init__.py` with
  `SupportsResponse.ONLY`.
- Tools within one coordinator are still fetched **sequentially**, so the
  SDK's 429 backoff has room to work.

## Testing locally

There's no npm build — it's a HA custom component. Test by copying
`custom_components/traderdaddy/` into a Home Assistant config dir (or symlink it),
restarting HA, and adding the integration via **Settings → Devices & Services**.
It works in demo mode with no key. HACS users install it as a custom repository.

For the Lovelace card, open `www/preview.html` directly in a browser (or run
it through Playwright) — no HA instance required, it stubs `hass` with mock
data.

## Conventions (match these)

- **Coordinators own all I/O; entities are pure reads** off a cached dict.
- **Keep the demo-first default** — `mock=True` when no key is configured.
- **Respect the slow cadence.** Don't shorten the intervals or fan out extra
  calls; this integration is deliberately gentle on the rate limit.
- **Python SDK method names are snake_case** (`market_stats()`, `unusual_activity()`,
  `gex_ticker()`) — the mirror of the TS SDK's camelCase.
- **`types.py` in the SDK is ground truth for field names.** Several TypedDicts
  are snake_case (e.g. `MarketStats`) even though most of the SDK's shapes are
  camelCase — don't assume, check `traderdaddy-sdk/traderdaddy-sdk/python/traderdaddy/types.py`.
- **Multi-ticker is out of scope for now.** Every tool that takes a symbol
  argument uses the single configured `symbol` — no per-symbol devices/config
  subentries yet (see `FINDINGS.md`).

## Gotchas

- **Key safety: self-host / personal.** The user's `td_live_` key lives in HA's
  config entry (entered via the config flow), on their own HA server. Never logged.
- **Depends on the `traderdaddy` PyPI SDK** (`manifest.json` requirements). If a
  method or response shape is missing, it's an upstream fix in
  `traderdaddy-sdk/python/`, not here.
- **TRMNL plugin is not built.** If a task mentions the e-ink device, that half is
  still a build brief (see the README) — the HA integration is what exists today.

## Where to look when unsure

- The Python SDK's methods → [`traderdaddy-sdk/python/README.md`](https://github.com/mphinance/traderdaddy-sdk/blob/main/python/README.md)
- HA integration patterns → [developers.home-assistant.io](https://developers.home-assistant.io)
- Prompts to customize this integration → [`PROMPTS.md`](PROMPTS.md)
