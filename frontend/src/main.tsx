import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import Plot from "react-plotly.js";
import "./style.css";

type ParticleInfo = {
  name: string;
  pdgid: number;
  mass_gev: number;
  charge: number | null;
  spin: number | null;
  width_gev: number | null;
};

type SuggestedResonance = {
  name: string;
  pdgid: number;
  pair: "12" | "13" | "23";
  mass_gev: number | null;
  width_gev: number | null;
  spin: number | null;
};

type DecayValidation = {
  allowed: boolean;
  channel: string;
  message: string;
  warnings: string[];
  transition_count: number;
  suggested_resonances: Record<"12" | "13" | "23", SuggestedResonance[]>;
};

type EventRow = {
  p1: [number, number, number, number];
  p2: [number, number, number, number];
  p3: [number, number, number, number];
  s12: number;
  s13: number;
  s23: number;
  phase_space_weight: number;
  amplitude_squared: number;
  total_weight: number;
};

type GenerateResponse = {
  mother: ParticleInfo;
  daughters: [ParticleInfo, ParticleInfo, ParticleInfo];
  unit: "GeV";
  events: EventRow[];
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

function App() {
  const [mother, setMother] = useState("D0");
  const [d1, setD1] = useState("pi+");
  const [d2, setD2] = useState("pi-");
  const [d3, setD3] = useState("pi0");
  const [nEvents, setNEvents] = useState(5000);
  const [seed, setSeed] = useState(7);
  const [validation, setValidation] = useState<DecayValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [data, setData] = useState<GenerateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setValidating(true);
      setValidationError(null);
      setValidation(null);
      setData(null);
      try {
        const response = await fetch(`${API_URL}/decays/validate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mother: { name: mother },
            daughters: [{ name: d1 }, { name: d2 }, { name: d3 }],
          }),
          signal: controller.signal,
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail ?? "Decay validation failed.");
        setValidation(payload as DecayValidation);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setValidationError(err instanceof Error ? err.message : "Unexpected validation error.");
      } finally {
        if (!controller.signal.aborted) setValidating(false);
      }
    }, 450);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [mother, d1, d2, d3]);

  async function generate(event: FormEvent) {
    event.preventDefault();
    if (!validation?.allowed) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/phase-space/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mother: { name: mother },
          daughters: [{ name: d1 }, { name: d2 }, { name: d3 }],
          n_events: nEvents,
          seed,
        }),
      });

      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Could not generate phase-space events.");
      setData(payload as GenerateResponse);
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Unexpected error.");
    } finally {
      setLoading(false);
    }
  }

  const arrays = useMemo(() => {
    const events = data?.events ?? [];
    return {
      s12: events.map((item) => item.s12),
      s13: events.map((item) => item.s13),
      s23: events.map((item) => item.s23),
    };
  }, [data]);

  return (
    <main>
      <header>
        <p className="eyebrow">Three-body decay playground</p>
        <h1>Dalitz Plot Web Visualizer</h1>
        <p className="lead">
          Validate the channel with <code>qrules</code>, resolve particle properties with <code>particle</code>,
          and generate physical four-momenta with <code>phasespace</code>.
        </p>
      </header>

      <form className="panel" onSubmit={generate}>
        <div className="section-heading">
          <div>
            <h2>Decay channel</h2>
            <p>The channel is checked automatically whenever a particle changes.</p>
          </div>
          <span className="badge">GeV units</span>
        </div>

        <div className="grid particles-grid">
          <Field label="Mother" value={mother} onChange={setMother} />
          <Field label="Daughter 1" value={d1} onChange={setD1} />
          <Field label="Daughter 2" value={d2} onChange={setD2} />
          <Field label="Daughter 3" value={d3} onChange={setD3} />
        </div>

        <div className={`validation-box ${validation?.allowed ? "allowed" : "forbidden"}`}>
          {validating && <strong>Checking with qrules…</strong>}
          {validationError && <strong>{validationError}</strong>}
          {validation && (
            <>
              <strong>{validation.allowed ? "✓ Allowed decay" : "✕ Decay not allowed"}</strong>
              <span>{validation.message}</span>
              {validation.allowed && <span>{validation.transition_count} allowed transitions found.</span>}
            </>
          )}
        </div>

        <div className="grid generation-grid">
          <label>
            Events
            <input type="number" min={1} max={1_000_000} value={nEvents}
              onChange={(event) => setNEvents(Number(event.target.value))} />
          </label>
          <label>
            Seed
            <input type="number" value={seed}
              onChange={(event) => setSeed(Number(event.target.value))} />
          </label>
          <button type="submit" disabled={loading || validating || !validation?.allowed}>
            {loading ? "Generating…" : "Generate phase space"}
          </button>
        </div>

        {error && <p className="error">{error}</p>}
      </form>

      {validation?.allowed && (
        <section className="panel">
          <h2>Suggested intermediate states</h2>
          <p className="muted">Suggestions come from qrules. Custom states can still be added later.</p>
          <div className="resonance-columns">
            {(["12", "13", "23"] as const).map((pair) => (
              <article key={pair}>
                <h3>Pair {pair}</h3>
                {validation.suggested_resonances[pair].length === 0 ? (
                  <p className="muted">No suggested states.</p>
                ) : (
                  <ul>
                    {validation.suggested_resonances[pair].map((item) => (
                      <li key={`${pair}-${item.pdgid}`}>
                        <strong>{item.name}</strong>
                        <span>{item.mass_gev == null ? "mass unavailable" : `${item.mass_gev.toFixed(4)} GeV`}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {data && (
        <>
          <section className="panel">
            <h2>Resolved particles</h2>
            <div className="particle-cards">
              {[data.mother, ...data.daughters].map((particle, index) => (
                <article key={`${particle.pdgid}-${index}`}>
                  <strong>{particle.name}</strong>
                  <span>PDG ID: {particle.pdgid}</span>
                  <span>Mass: {particle.mass_gev.toFixed(6)} GeV</span>
                </article>
              ))}
            </div>
          </section>

          <section className="panel plot-panel">
            <h2>Dalitz plot</h2>
            <Plot data={[{ x: arrays.s12, y: arrays.s13, mode: "markers", type: "scattergl",
              marker: { size: 4, opacity: 0.55 },
              text: arrays.s23.map((value) => `s23 = ${value.toFixed(4)} GeV²`),
              hovertemplate: "s12=%{x:.4f}<br>s13=%{y:.4f}<br>%{text}<extra></extra>" }]}
              layout={{ autosize: true, margin: { l: 65, r: 20, t: 20, b: 55 },
                xaxis: { title: { text: "s12 [GeV²]" } }, yaxis: { title: { text: "s13 [GeV²]" } } }}
              config={{ responsive: true }} style={{ width: "100%", height: "520px" }} useResizeHandler />
          </section>

          <section className="projections">
            {(["s12", "s13", "s23"] as const).map((key) => (
              <div className="panel" key={key}>
                <h2>{key} projection</h2>
                <Plot data={[{ x: arrays[key], type: "histogram", nbinsx: 60 }]}
                  layout={{ autosize: true, margin: { l: 50, r: 15, t: 15, b: 50 },
                    xaxis: { title: { text: `${key} [GeV²]` } }, yaxis: { title: { text: "Events" } } }}
                  config={{ responsive: true }} style={{ width: "100%", height: "300px" }} useResizeHandler />
              </div>
            ))}
          </section>
        </>
      )}
    </main>
  );
}

function Field(props: { label: string; value: string; onChange: (value: string) => void }) {
  return <label>{props.label}<input value={props.value}
    onChange={(event) => props.onChange(event.target.value)} required /></label>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
