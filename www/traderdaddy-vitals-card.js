/**
 * TraderDaddy Pro — Vitals Card
 *
 * Vanilla-JS custom Lovelace card. No build step (matches the trick
 * DaddyBoard already proved for its wall-display client): drop this file in
 * `www/`, add it as a dashboard resource, done.
 *
 * Add as a Home Assistant dashboard resource:
 *   Settings -> Dashboards -> (three dots) -> Resources -> Add Resource
 *     URL: /local/traderdaddy-vitals-card.js
 *     Type: JavaScript Module
 *
 * Then add a card:
 *   type: custom:traderdaddy-vitals-card
 *   (optional) entities: { sentiment: sensor.xyz, ... } to override auto-detected ids
 *
 * Design language mirrors DaddyBoard's dark glassmorphism: navy base,
 * translucent panels, neon gold accent, neon green/red for bull/bear.
 */

const DEFAULT_ENTITIES = {
  sentiment: "sensor.td_market_sentiment",
  put_call: "sensor.td_put_call_ratio",
  gamma_bias: "sensor.td_gamma_bias",
  top_flow: "sensor.td_top_flow",
  institutional_leader: "sensor.td_institutional_leader",
  conviction_market: "sensor.td_conviction_market",
  legendary_print: "binary_sensor.td_legendary_print",
  gamma_flip: "binary_sensor.td_gamma_flip",
};

const STYLE = `
  :host {
    --td-bg-base: hsl(222 42% 7%);
    --td-panel-fill: hsla(220 40% 12% / 0.66);
    --td-border: hsla(210 30% 70% / 0.10);
    --td-accent: hsl(40 96% 56%);
    --td-accent-dim: hsla(40 96% 56% / 0.14);
    --td-bull: hsl(150 85% 50%);
    --td-bear: hsl(2 90% 62%);
    --td-caution: hsl(42 96% 56%);
    --td-text-primary: hsl(210 25% 96%);
    --td-text-muted: hsl(210 15% 62%);
  }
  ha-card {
    background:
      radial-gradient(ellipse 120% 60% at 50% 0%, hsla(214 90% 58% / 0.10) 0%, transparent 65%),
      var(--td-bg-base);
    color: var(--td-text-primary);
    border: 1px solid var(--td-border);
    border-radius: 16px;
    padding: 16px 18px;
    font-family: var(--paper-font-body1_-_font-family, sans-serif);
    overflow: hidden;
  }
  .td-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
  }
  .td-title {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--td-text-muted);
  }
  .td-title span { color: var(--td-accent); }
  .td-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    background: var(--td-accent-dim);
    color: var(--td-accent);
    border: 1px solid hsla(40 96% 56% / 0.35);
  }
  .td-badge.is-off { opacity: 0.35; }
  .td-badge.is-legendary {
    background: hsla(40 96% 56% / 0.22);
    box-shadow: 0 0 14px hsla(40 96% 56% / 0.35);
    animation: td-pulse 1.6s ease-in-out infinite;
  }
  @keyframes td-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.55; }
  }
  .td-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .td-tile {
    background: var(--td-panel-fill);
    border: 1px solid var(--td-border);
    border-radius: 12px;
    padding: 10px 12px;
    min-width: 0;
  }
  .td-tile-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--td-text-muted);
    margin-bottom: 4px;
  }
  .td-tile-value {
    font-size: 18px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .td-tile-sub {
    font-size: 11px;
    color: var(--td-text-muted);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .bull { color: var(--td-bull); }
  .bear { color: var(--td-bear); }
  .neutral { color: var(--td-caution); }
  .unavailable { color: var(--td-text-muted); font-style: italic; }
`;

function sentimentClass(value) {
  const v = String(value || "").toLowerCase();
  if (v.includes("bull")) return "bull";
  if (v.includes("bear")) return "bear";
  return "neutral";
}

function biasClass(value) {
  const v = String(value || "").toUpperCase();
  if (v.includes("SHORT")) return "bear";
  if (v.includes("LONG")) return "bull";
  return "neutral";
}

class TraderDaddyVitalsCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._entities = { ...DEFAULT_ENTITIES, ...(config.entities || {}) };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  _state(entityId) {
    if (!this._hass) return undefined;
    return this._hass.states[entityId];
  }

  _render() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }

    const e = this._entities || DEFAULT_ENTITIES;
    const sentiment = this._state(e.sentiment);
    const putCall = this._state(e.put_call);
    const gamma = this._state(e.gamma_bias);
    const topFlow = this._state(e.top_flow);
    const institutional = this._state(e.institutional_leader);
    const conviction = this._state(e.conviction_market);
    const legendary = this._state(e.legendary_print);
    const gammaFlip = this._state(e.gamma_flip);

    const val = (s, fallback = "—") => (s && s.state !== undefined ? s.state : fallback);
    const attr = (s, key, fallback = "") => (s && s.attributes ? s.attributes[key] ?? fallback : fallback);

    const legendaryOn = legendary && legendary.state === "on";
    const gammaFlipOn = gammaFlip && gammaFlip.state === "on";

    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card>
        <div class="td-header">
          <div class="td-title">Trader<span>Daddy</span> Pro — Vitals</div>
          <div class="td-badge ${legendaryOn ? "is-legendary" : "is-off"}">
            ${legendaryOn ? "🔥 Legendary print" : "No legendary print"}
          </div>
        </div>
        <div class="td-grid">
          <div class="td-tile">
            <div class="td-tile-label">Market sentiment</div>
            <div class="td-tile-value ${sentimentClass(val(sentiment))}">${val(sentiment)}</div>
            <div class="td-tile-sub">SPY P/C ${attr(sentiment, "spy_put_call_ratio", "—")}</div>
          </div>
          <div class="td-tile">
            <div class="td-tile-label">Put/call ratio</div>
            <div class="td-tile-value">${val(putCall)}</div>
            <div class="td-tile-sub">Symbol read</div>
          </div>
          <div class="td-tile">
            <div class="td-tile-label">Gamma bias</div>
            <div class="td-tile-value ${biasClass(val(gamma))} ${gammaFlipOn ? "bear" : ""}">
              ${gammaFlipOn ? "⚠ " : ""}${val(gamma)}
            </div>
            <div class="td-tile-sub">${gammaFlipOn ? "Short gamma — expect chop" : "Dealer positioning"}</div>
          </div>
          <div class="td-tile">
            <div class="td-tile-label">Top flow</div>
            <div class="td-tile-value">${val(topFlow)}</div>
            <div class="td-tile-sub">${attr(topFlow, "tier", "")} ${attr(topFlow, "flow_description", "")}</div>
          </div>
          <div class="td-tile">
            <div class="td-tile-label">Institutional leader</div>
            <div class="td-tile-value">${val(institutional)}</div>
            <div class="td-tile-sub">${attr(institutional, "sentiment", "")}</div>
          </div>
          <div class="td-tile">
            <div class="td-tile-label">Market conviction</div>
            <div class="td-tile-value">${val(conviction)}</div>
            <div class="td-tile-sub">Composite score</div>
          </div>
        </div>
      </ha-card>
    `;
  }
}

customElements.define("traderdaddy-vitals-card", TraderDaddyVitalsCard);

// Card picker registration (best-effort — harmless if window.customCards is unavailable).
window.customCards = window.customCards || [];
window.customCards.push({
  type: "traderdaddy-vitals-card",
  name: "TraderDaddy Pro Vitals",
  description: "Sentiment, gamma bias, top flow, and conviction at a glance.",
});
