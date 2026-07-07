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
| `custom_components/traderdaddy/__init__.py` | Entry setup/unload; creates the coordinator. |
| `custom_components/traderdaddy/config_flow.py` | UI config flow — the user's `td_live_` key + symbol. |
| `custom_components/traderdaddy/coordinator.py` | `DataUpdateCoordinator` — one poll cycle fetches all tools; the **one** SDK instance. |
| `custom_components/traderdaddy/sensor.py` | Sensors — each is one `value_fn`/`attr_fn` over the coordinator's cache. |
| `custom_components/traderdaddy/binary_sensor.py` | Binary sensors (e.g. market open). |
| `custom_components/traderdaddy/entity.py` | Shared base entity. |
| `custom_components/traderdaddy/const.py` | `DOMAIN`, conf keys, `SCAN_INTERVAL_OPEN/CLOSED`, `PLATFORMS`. |
| `custom_components/traderdaddy/manifest.json` | HA manifest — `requirements: ["traderdaddy>=0.1.0"]`. |
| `custom_components/traderdaddy/strings.json` + `translations/` | Config-flow UI strings. |
| `hacs.json` | HACS metadata (custom-repo install). |

## The one rule

`coordinator.py` is the **only** place the SDK is instantiated. One
`_async_update_data` cycle fetches the whole tool set into a dict; every sensor
reads from that cached dict via its `value_fn` — **sensors never call the SDK
directly.** Adding a sensor = one `SensorEntityDescription` with a `value_fn`, no
new polling.

## How it runs

- **No key → keyless demo** (`TraderDaddy(mock=True)`) — the funnel default. With
  a key, `TraderDaddy(api_key=…, client=get_async_client(hass))` shares HA's own
  httpx client rather than spinning up its own.
- **Market-hours cadence:** `SCAN_INTERVAL_OPEN` = 2 min, `SCAN_INTERVAL_CLOSED`
  = 15 min, re-tuned each cycle from `is_market_open()`. E-ink / smart-home reads
  don't need to be fast, and slow polling stays well under the per-key rate limit.
- **Tools polled each cycle** (sequentially, so the SDK's 429 backoff has room):
  `market_stats`, `unusual_activity(limit=10)`, `gex_overview`, `iv_rank(symbol)`,
  `sector_flow`, `put_call_ratios(symbol)`.

## Testing locally

There's no npm build — it's a HA custom component. Test by copying
`custom_components/traderdaddy/` into a Home Assistant config dir (or symlink it),
restarting HA, and adding the integration via **Settings → Devices & Services**.
It works in demo mode with no key. HACS users install it as a custom repository.

## Conventions (match these)

- **Coordinator owns all I/O; sensors are pure reads** off its cached dict.
- **Keep the demo-first default** — `mock=True` when no key is configured.
- **Respect the slow cadence.** Don't shorten the intervals or fan out extra
  calls; this integration is deliberately gentle on the rate limit.
- **Python SDK method names are snake_case** (`market_stats()`, `unusual_activity()`,
  `gex_ticker()`) — the mirror of the TS SDK's camelCase.

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
