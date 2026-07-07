# Prompt pack — make DaddyHome yours

DaddyHome brings TraderDaddy Pro into Home Assistant as sensors (with a TRMNL
e-ink plugin planned). Pick a prompt, paste it into your AI coding tool (Claude
Code, Cursor, …) inside a clone of this repo, and let it drive. The integration
runs in **keyless demo mode**, so you can develop with no key.

> **First, always:** tell your AI to read `CLAUDE.md` in this repo.

---

## 1. Add a new sensor

```
I want to add a new Home Assistant sensor to this integration. Read CLAUDE.md
first — the coordinator is the ONLY thing that calls the SDK; sensors are pure
reads over its cached dict via a value_fn.

The sensor: [describe it — e.g. "sector with the strongest inflow today" /
"IV percentile for my symbol" / "count of active alerts"].

Steps:
1. If the data is already fetched in coordinator.py's _async_update_data, just add
   a SensorEntityDescription with a value_fn in sensor.py. DON'T add a new poll
   unless the tool isn't already fetched.
2. If it IS a new tool, add it to the coordinator's one fetch cycle (sequential,
   keep the slow cadence) and a matching snake_case SDK method.
3. Add UI strings for it if needed (strings.json / translations/en.json).
Explain the plan first. Remind me how to reload it in Home Assistant to test in
demo mode.
```

---

## 2. Adjust the polling cadence

```
I want to change how often the integration polls. Read CLAUDE.md and const.py +
coordinator.py first.

What I want: [e.g. "poll every minute while the market is open" / "stop polling
entirely overnight"].

Keep it rate-limit-friendly — this integration is deliberately gentle, and the
cadence re-tunes from is_market_open() each cycle. Explain the tradeoff (faster =
more API calls against my key's limit) before changing SCAN_INTERVAL_OPEN/CLOSED.
```

---

## 3. Install it in your Home Assistant

```
I'm a beginner and I want to install this integration in my Home Assistant. Read
CLAUDE.md and the README first. Walk me through:
1. Installing via HACS as a custom repository (hacs.json is set up), OR copying
   custom_components/traderdaddy/ into my HA config dir manually.
2. Restarting HA and adding "TraderDaddy Pro" via Settings → Devices & Services.
3. Running it in demo mode first (no key), then where to paste my own td_live_ key
   in the config flow to go live.
4. A simple automation idea using one of the sensors (e.g. flash a light on a big
   flow print).
Explain each step; assume I've installed a HACS integration before but nothing
about this one.
```

---

## 4. Build the TRMNL e-ink plugin (not built yet)

```
The TRMNL e-ink plugin half of this repo isn't built yet — I want to start it.
Read CLAUDE.md and the README's TRMNL section first.

TRMNL takes a polling URL that returns markup/JSON. Since TRMNL renders server-
side, help me build a tiny Node service using the TypeScript @traderdaddy/sdk
(NOT the Python one — that's for the HA half) that returns a glanceable e-ink
layout: market vitals, put/call, gamma bias, top flow print. Build it keyless
(mock: true) first so I can see the layout with no key, on a slow poll cadence
(e-ink is low-refresh). Show me the plan before writing code.
```

---

## 5. Contribute your improvement back

```
I made a change others would want. Help me contribute it back as a pull request.
Read CLAUDE.md first and match its conventions (coordinator owns I/O, sensors are
pure reads, keep the slow cadence, demo-first default).

Before the PR:
1. Load the integration in a test Home Assistant and confirm it starts in demo
   mode without errors.
2. Confirm no API key is committed anywhere.
3. Help me write a clear commit message and open the PR against `main` on GitHub.
Explain each step.
```

---

## Tips

- **It runs keyless.** No key → demo mode, so you can develop and test the whole
  integration with no key. Add yours in the config flow only for live data.
- **The coordinator is the only thing that calls the SDK.** If your AI adds a
  `TraderDaddy(...)` inside a sensor, tell it to read from the coordinator's
  cached data instead.
- **Keep polling slow.** Faster cadence burns your key's rate limit for data that
  barely changes minute to minute.
- **Two SDKs, two languages.** The HA integration uses the **Python** `traderdaddy`
  SDK (snake_case methods). The planned TRMNL service would use the **TypeScript**
  `@traderdaddy/sdk`. Don't mix them.
