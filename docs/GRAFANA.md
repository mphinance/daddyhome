# Long-term trend: InfluxDB + Grafana

HA's built-in recorder is great for the last ~10 days, but it purges
aggressively — not useful for "how has NVDA's conviction score trended over
the last quarter." This recipe pipes TraderDaddy Pro's sensors into InfluxDB
so Grafana can chart them indefinitely, alongside anything else already on
your Grafana instance.

## 1. Add the InfluxDB integration

`Settings -> Devices & Services -> Add Integration -> InfluxDB` (or via YAML,
see [HA's `influxdb` docs](https://www.home-assistant.io/integrations/influxdb/)).
Point it at your InfluxDB instance and scope it to just this integration's
entities so you're not shipping your whole HA state history:

```yaml
influxdb:
  host: localhost
  port: 8086
  database: homeassistant
  include:
    domains:
      - sensor
      - binary_sensor
    entity_globs:
      - sensor.traderdaddy_pro_*
      - binary_sensor.traderdaddy_pro_*
```

Every coordinator poll (2–15 min for fast-tier, 10–30 min for slow-tier —
see the main README) writes a new point per sensor. Numeric sensors
(`conviction_market`, `bounce_score_symbol`, `long_term_quality`, etc.) chart
directly; string-state sensors (`market_sentiment`, `gamma_bias`) are best
charted as a state-timeline panel.

## 2. Add InfluxDB as a Grafana data source

`Grafana -> Connections -> Data sources -> Add data source -> InfluxDB`.
Point it at the same database HA is writing to. Use Flux or InfluxQL
depending on your InfluxDB version — the exported dashboard below assumes
InfluxQL (matches HA's default `influxdb` integration writer).

## 3. Import the dashboard

`Grafana -> Dashboards -> Import`, upload
[`grafana-dashboard.json`](./grafana-dashboard.json), select your InfluxDB
data source when prompted. It ships four panels:

| Panel | Source sensor | What it shows |
|---|---|---|
| Market conviction (trend) | `sensor.traderdaddy_pro_conviction_market` | Composite conviction score over time |
| Symbol conviction vs. quality | `sensor.traderdaddy_pro_conviction_symbol`, `sensor.traderdaddy_pro_long_term_quality` | Tracked-symbol conviction alongside its long-term quality score |
| Sentiment timeline | `sensor.traderdaddy_pro_market_sentiment` | State-timeline of bullish/bearish/neutral over the day |
| Legendary print frequency | `binary_sensor.traderdaddy_pro_legendary_print` | On/off state history — how often the tape prints LEGENDARY |

Adjust entity ids in the dashboard's variables if your instance has more
than one TraderDaddy Pro config entry (each entry's device name suffixes the
entity id if you add a second one).

## Notes

- This is a docs-only deliverable — no code in this repo talks to InfluxDB
  directly. HA's own `influxdb` integration does the writing; this file just
  saves you from hand-building the dashboard.
- If you don't run InfluxDB/Grafana, none of this is required — the HA
  sensors, the custom Lovelace card, and the calendar entities all work
  standalone.
