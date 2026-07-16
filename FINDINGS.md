# FINDINGS — daddyhome expansion ideas (2026-07-16, recon pass)

Ideation only — nothing here is built. Written after reading the live SDK
client (`traderdaddy-sdk/traderdaddy-sdk/python/traderdaddy/client.py`),
DaddyBoard's `SPEC.md`/`STATUS.md`, and the current `daddyhome` sensor/binary
sensor/coordinator code.

**Key correction to prior memory:** the SDK is not 12 tools, it's **24**.
daddyhome currently polls 6. 18 tools have zero HA presence.

## The 18 uncovered tools

| tool | shape | HA entity idea |
|---|---|---|
| `run_screener(screener)` | 10 named screeners (bullish-pullback, momentum, volatility-squeeze, small-cap, volatility-surge, gamma-scan, csp-wheel, leaps, leveraged, daily-cuts) | one sensor per screener OR a rotating "screener of the cycle" sensor (mirrors DaddyBoard's rotating main-stage) |
| `strategy_ideas(symbol)` | ranked options-strategy ideas | sensor: top idea label, attrs = full ranked list |
| `edge_xray(symbol)` | rich/cheap contract residuals | sensor: richest/cheapest contract, attrs = full table |
| `earnings_flow(days)` | pre-earnings flow window | sensor + **calendar entity** (see below) |
| `economic_calendar()` | macro calendar | **calendar entity** — native HA fit |
| `apex_levels(symbol)` | magnet strike ranking | sensor: top magnet strike + attrs |
| `politician_trades()` / `politician_trades_by_ticker()` | Congressional disclosures | sensor (latest trade) + `event` entity (new trade lands) |
| `institutional_activity()` | top institutional flow names ex-MAG7/ETF | sensor: top name, attrs = ranked list |
| `dividend_calendar()` | upcoming ex-div dates | **calendar entity** |
| `long_term_quality(symbol)` | fundamental/dividend quality screener | sensor per watched symbol |
| `ipo_scanner(view)` | upcoming/recent/radar/transitions | sensor + `event` entity for new IPO listing |
| `bounce_signals()` / `bounce_score(symbol)` | oversold/overbought composite | sensor, binary_sensor for "bounce triggered" |
| `conviction(symbol?)` | community conviction gauge | sensor (market-wide + per-symbol) |
| `market_health()` | 7-detector macro risk composite | sensor — good gauge-card candidate |
| `hedge_analysis(symbol, shares, ...)` | ranked hedge structures for a position | **service**, not a sensor (needs args at call time — see below) |
| `gex_ticker(symbol)` | per-symbol gamma ladder | sensor (currently only `gex_overview` market-wide is used) |

## Quick wins (low effort, high value)

1. **`market_health` sensor** — single composite risk score, trivial value_fn, great gauge-card material.
2. **`gex_ticker(symbol)`** for the configured symbol — same shape as existing `iv_rank`/`put_call_ratios` per-symbol pattern, drop-in.
3. **`institutional_activity` top-name sensor** — same shape as existing `top_flow`.
4. **`conviction()` market-wide sensor** — same shape as `market_sentiment`.
5. **Rotating screener sensor** — one coordinator poll of `run_screener`, rotate the screener key each cycle (DaddyBoard already proved this pattern at 300s cadence). One sensor, ten screeners' worth of value.

## Automation hooks — more binary_sensor / event entities

Today there's exactly one (`binary_sensor.td_legendary_print`). Ideas, roughly
DaddyBoard-panel-inspired but built for *triggering things* rather than display:

- `binary_sensor.td_gamma_flip` — on when `gex_overview.marketSummary.bias` flips sign since last poll.
- `binary_sensor.td_elevated_risk` — on when `market_health()` composite crosses a configurable threshold.
- `binary_sensor.td_bounce_signal` — on when `bounce_score(symbol)` crosses into oversold/overbought territory for the watched symbol.
- `binary_sensor.td_high_conviction` — on when community conviction for the watched symbol spikes.
- New HA `event` platform entities (HA's native "discrete thing happened" type, distinct from binary_sensor's on/off state) for feed-shaped data:
  - `event.td_new_print` — fires per new unusual-activity row, `event_type` = tier (ELITE/LEGENDARY/etc). Generalizes the existing LEGENDARY-only binary sensor to the full tape.
  - `event.td_new_politician_trade`
  - `event.td_new_ipo_listing`
  - `event.td_earnings_approaching` — X days out from the watched symbol's earnings date

This is the single most HA-native way to get "a whole lot more" automation
surface without turning every tool into a noisy polling sensor.

## Multi-ticker architecture (bigger lift, real payoff)

Config flow today takes exactly one `symbol`. Every ticker-scoped tool
(`gex_ticker`, `iv_rank`, `edge_xray`, `apex_levels`, `strategy_ideas`,
`bounce_score`, `conviction`, `long_term_quality`) is capped at that one
symbol. HA supports **config subentries** — add a "watched ticker" subentry
flow so a user can add NVDA, SPY, META as separate devices, each getting its
own set of ticker-scoped sensors, each on its own coordinator (or a shared
coordinator keyed by symbol). This is the biggest structural idea on this
list and probably deserves its own build wave before entity sprawl.

## The "DaddyBoard pieces in HA" / "Grafana-like" bucket

Three different sizes of the same idea, cheapest first:

1. **Native `calendar` entities** (cheapest, most HA-idiomatic). `economic_calendar`,
   `earnings_flow`, `dividend_calendar` are all literally calendar-shaped data.
   HA has a first-class `calendar` platform — events show up in HA's own
   calendar dashboard card and can drive "notify me 1 day before FOMC"
   automations for free. Nothing like this exists in DaddyBoard (web
   dashboard has no calendar widget) — this is daddyhome doing something the
   web board can't.
2. **Long-term trend via InfluxDB + a shipped Grafana dashboard JSON** (medium
   effort, matches what mph means by "people love grafana-like things in
   HA"). HA's own recorder purges after ~10 days; the community's answer is
   always "pipe to InfluxDB, graph in Grafana." Ship a
   `docs/grafana-dashboard.json` + a short recipe (HA's built-in `influxdb:`
   integration config) so total flow premium, gamma bias, sentiment score,
   and market_health trend over months instead of days. This is documentation
   + one JSON file, not code — very cheap for a lot of "wow."
3. **A real custom Lovelace card** (highest effort, closest to "DaddyBoard
   pieces ported in"). A small bundled `www/traderdaddy-vitals-card.js`
   (vanilla JS, no build step — same constraint DaddyBoard already proved
   works) rendering a mini glassmorphism vitals tile: sentiment gauge + top
   flow ticker + gamma bias, dark theme, matching DaddyBoard's design-token
   aesthetic. Registered via `frontend.add_extra_js_url`, HACS-installable
   alongside the integration. This is the one that actually looks like "daddy
   board in my house."

## Power-user idea: HA services with response data

`hedge_analysis(symbol, shares, basis?, atr?)` doesn't fit a polling sensor —
it needs call-time args. HA services with response data (2024.8+) are the
right primitive: register `traderdaddy.hedge_analysis` as a callable service
from Developer Tools / scripts / automations, returns the ranked hedge
structures as response data. Same pattern could expose `run_screener` and
`edge_xray` on-demand rather than only via polling.

## Smaller UX ideas

- **Select/number helper entity** to change the watched symbol from the HA UI without editing config flow (re-triggers a targeted refresh of ticker-scoped tools only).
- **Markdown "daily brief" sensor** — short state + long markdown attribute (mirrors the MUR premarket-brief pattern from another repo), rendered nicely by HA's native markdown card. Sensor state stays under HA's 255-char limit; the markdown lives in an attribute.

## Suggested priority order (my read, not a decision)

1. Quick-win sensors (market_health, gex_ticker, institutional_activity, conviction) — same pattern as existing code, near-zero risk.
2. Event entities for the flow tape + politician trades / IPOs — generalizes the one binary_sensor pattern that already works.
3. Calendar entities (economic/earnings/dividend) — cheap, HA-idiomatic, nothing like it exists elsewhere in the family.
4. Grafana/InfluxDB recipe doc — cheap, high perceived value, no code risk.
5. Multi-ticker config subentries — bigger lift, unlocks everything ticker-scoped, worth doing before more ticker sensors pile onto one symbol.
6. Custom Lovelace vitals card — the marquee "DaddyBoard in HA" piece, highest effort.
7. `hedge_analysis` / on-demand services — nice-to-have, not urgent.

Bring this back to mph before building anything.
