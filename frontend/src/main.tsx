import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import Plot from "react-plotly.js";
import "./style.css";

type ParticleInfo = {
  name: string; pdgid: number; mass_gev: number;
  charge: number | null; spin: number | null; width_gev: number | null;
};
type SuggestedResonance = {
  name: string; pdgid: number; pair: "12" | "13" | "23";
  mass_gev: number | null; width_gev: number | null; spin: number | null;
};
type ResonanceConfig = {
  id: string; name: string; pair: "12" | "13" | "23";
  spin: number; mass: number; width: number; lineshape: "RBW";
  magnitude: number; phase_deg: number; resonance_radius: number; mother_radius: number; source: "suggested";
};
type DecayValidation = {
  allowed: boolean; channel: string; message: string; warnings: string[];
  transition_count: number;
  suggested_resonances: Record<"12" | "13" | "23", SuggestedResonance[]>;
};
type EventRow = {
  p1: [number, number, number, number]; p2: [number, number, number, number];
  p3: [number, number, number, number]; s12: number; s13: number; s23: number;
  phase_space_weight: number; amplitude_squared: number; total_weight: number;
};
type ComponentNormalization = { key: string; integral: number; amplitude_scale: number };
type GenerateResponse = {
  mother: ParticleInfo; daughters: [ParticleInfo, ParticleInfo, ParticleInfo];
  unit: "GeV"; symmetrized: boolean; symmetry_term_count: number;
  components_normalized: boolean; component_normalizations: ComponentNormalization[]; events: EventRow[];
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
const pairTuple: Record<"12" | "13" | "23", [number, number]> = {
  "12": [1, 2], "13": [1, 3], "23": [2, 3],
};

function App() {
  const [mother, setMother] = useState("D0");
  const [d1, setD1] = useState("pi+");
  const [d2, setD2] = useState("pi-");
  const [d3, setD3] = useState("pi0");
  const [nEvents, setNEvents] = useState(10000);
  const [seed, setSeed] = useState(7);
  const [validation, setValidation] = useState<DecayValidation | null>(null);
  const [resonances, setResonances] = useState<ResonanceConfig[]>([]);
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [data, setData] = useState<GenerateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setValidating(true); setValidationError(null); setValidation(null);
      setResonances([]); setData(null);
      try {
        const response = await fetch(`${API_URL}/decays/validate`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mother: { name: mother }, daughters: [{ name: d1 }, { name: d2 }, { name: d3 }],
          }), signal: controller.signal,
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail ?? "Decay validation failed.");
        setValidation(payload as DecayValidation);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setValidationError(err instanceof Error ? err.message : "Unexpected validation error.");
      } finally { if (!controller.signal.aborted) setValidating(false); }
    }, 450);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [mother, d1, d2, d3]);

  function toggleResonance(item: SuggestedResonance) {
    const id = `${item.pair}:${item.pdgid}`;
    setResonances((current) => {
      if (current.some((resonance) => resonance.id === id)) {
        return current.filter((resonance) => resonance.id !== id);
      }
      if (item.mass_gev == null || item.width_gev == null || item.width_gev <= 0) return current;
      return [...current, {
        id, name: item.name, pair: item.pair, spin: Math.round(item.spin ?? 0),
        mass: item.mass_gev, width: item.width_gev, lineshape: "RBW",
        magnitude: 1.0, phase_deg: 0.0, resonance_radius: 1.5, mother_radius: 5.0, source: "suggested",
      }];
    });
  }

  function updateResonance(id: string, field: "magnitude" | "phase_deg" | "resonance_radius" | "mother_radius", value: number) {
    setResonances((current) => current.map((item) => item.id === id ? { ...item, [field]: value } : item));
  }

  async function generate(event?: FormEvent) {
    event?.preventDefault();
    if (!validation?.allowed) return;
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_URL}/phase-space/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mother: { name: mother }, daughters: [{ name: d1 }, { name: d2 }, { name: d3 }],
          n_events: nEvents, seed, symmetrize: true, normalize_components: true,
          resonances: resonances.map(({ id: _id, pair, ...item }) => ({ ...item, pair: pairTuple[pair] })),
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Could not generate weighted events.");
      setData(payload as GenerateResponse);
    } catch (err) {
      setData(null); setError(err instanceof Error ? err.message : "Unexpected error.");
    } finally { setLoading(false); }
  }

  const modelRevision = JSON.stringify(
    resonances.map(({ id, magnitude, phase_deg, resonance_radius, mother_radius }) => ({ id, magnitude, phase_deg, resonance_radius, mother_radius })),
  );

  useEffect(() => {
    if (!data || !validation?.allowed) return;
    const timer = window.setTimeout(() => { void generate(); }, 350);
    return () => window.clearTimeout(timer);
    // Regenerate only when the selected amplitude model changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modelRevision]);

  const arrays = useMemo(() => {
    const events = data?.events ?? [];
    return {
      s12: events.map((item) => item.s12), s13: events.map((item) => item.s13),
      s23: events.map((item) => item.s23), weights: events.map((item) => item.total_weight),
      intensity: events.map((item) => item.amplitude_squared),
    };
  }, [data]);

  return <main>
    <header><p className="eyebrow">Three-body decay playground</p><h1>Dalitz Plot Web Visualizer</h1>
      <p className="lead">Build a coherent resonance model and explore how magnitudes and phases reshape the Dalitz distribution.</p></header>

    <form className="panel" onSubmit={generate}>
      <div className="section-heading"><div><h2>Decay channel</h2><p>Checked automatically with qrules.</p></div><span className="badge">GeV units</span></div>
      <div className="grid particles-grid">
        <Field label="Mother" value={mother} onChange={setMother}/><Field label="Daughter 1" value={d1} onChange={setD1}/>
        <Field label="Daughter 2" value={d2} onChange={setD2}/><Field label="Daughter 3" value={d3} onChange={setD3}/>
      </div>
      <div className={`validation-box ${validation?.allowed ? "allowed" : "forbidden"}`}>
        {validating && <strong>Checking with qrules…</strong>}{validationError && <strong>{validationError}</strong>}
        {validation && <><strong>{validation.allowed ? "✓ Allowed decay" : "✕ Decay not allowed"}</strong><span>{validation.message}</span>
          {validation.allowed && <span>{validation.transition_count} allowed transitions found.</span>}</>}
      </div>
      <div className="grid generation-grid"><label>Events<input type="number" min={1} max={1_000_000} value={nEvents} onChange={(e)=>setNEvents(Number(e.target.value))}/></label>
        <label>Seed<input type="number" value={seed} onChange={(e)=>setSeed(Number(e.target.value))}/></label>
        <button type="submit" disabled={loading || validating || !validation?.allowed}>{loading ? "Generating…" : "Generate weighted Dalitz"}</button></div>
      {error && <p className="error">{error}</p>}
    </form>

    {validation?.allowed && <section className="panel">
      <div className="section-heading"><div><h2>Resonance model</h2><p>Select suggested states. RBW terms include dynamic widths, Blatt-Weisskopf factors and Zemach angular terms for spin 0, 1 and 2.</p></div>
        <span className="badge">{resonances.length} selected</span></div>
      <div className="resonance-columns">{(["12","13","23"] as const).map((pair)=><article key={pair}><h3>Pair {pair}</h3>
        {validation.suggested_resonances[pair].length===0 ? <p className="muted">No suggested states.</p> : <ul>
          {validation.suggested_resonances[pair].map((item)=>{
            const id=`${pair}:${item.pdgid}`; const selected=resonances.some((r)=>r.id===id); const enabled=item.mass_gev!=null && item.width_gev!=null && item.width_gev>0;
            return <li key={id} className={selected ? "selected" : ""}><label className="resonance-choice"><input type="checkbox" checked={selected} disabled={!enabled} onChange={()=>toggleResonance(item)}/>
              <span><strong>{item.name}</strong><small>{item.mass_gev?.toFixed(4) ?? "?"} GeV · Γ {item.width_gev?.toFixed(4) ?? "?"} GeV</small></span></label></li>;
          })}</ul>}</article>)}</div>

      {resonances.length>0 && <div className="selected-model"><h3>Selected amplitudes</h3><p className="muted">Each complete, symmetrized basis amplitude is normalized so that ∫dΦ₃ |Fᵣ|² = 1 before its complex coefficient is applied.</p>{resonances.map((resonance)=><div className="resonance-editor" key={resonance.id}>
        <div><strong>{resonance.name}</strong><span>pair {resonance.pair} · spin {resonance.spin} · dynamic RBW</span></div>
        <label>Magnitude<input type="number" step="0.05" min="0" value={resonance.magnitude} onChange={(e)=>updateResonance(resonance.id,"magnitude",Number(e.target.value))}/></label>
        <label>Phase [deg]<input type="range" min="-180" max="180" step="1" value={resonance.phase_deg} onChange={(e)=>updateResonance(resonance.id,"phase_deg",Number(e.target.value))}/><output>{resonance.phase_deg}°</output></label>
        <label>Resonance radius [GeV⁻¹]<input type="number" min="0.01" step="0.1" value={resonance.resonance_radius} onChange={(e)=>updateResonance(resonance.id,"resonance_radius",Number(e.target.value))}/></label>
        <label>Mother radius [GeV⁻¹]<input type="number" min="0.01" step="0.1" value={resonance.mother_radius} onChange={(e)=>updateResonance(resonance.id,"mother_radius",Number(e.target.value))}/></label>
      </div>)}</div>}
    </section>}

    {data && <>{data.symmetrized && <section className="panel symmetry-note"><strong>Identical-particle symmetrization active</strong><span>The complex amplitude includes {data.symmetry_term_count} distinct isobar assignments before |A|² is calculated.</span></section>}<section className="panel plot-panel"><div className="section-heading"><div><h2>Weighted Dalitz plot</h2><p>Marker colour represents |A|²; projections use the full phase-space × amplitude weight.</p></div></div>
      <Plot data={[{x:arrays.s12,y:arrays.s13,mode:"markers",type:"scattergl",marker:{size:5,opacity:.7,color:arrays.intensity,colorscale:"Viridis",showscale:true,colorbar:{title:{text:"|A|²"}}},
        text:arrays.s23.map((v,i)=>`s23=${v.toFixed(4)} GeV²<br>weight=${arrays.weights[i].toExponential(3)}`),hovertemplate:"s12=%{x:.4f}<br>s13=%{y:.4f}<br>%{text}<extra></extra>"}]}
        layout={{autosize:true,margin:{l:65,r:40,t:20,b:55},xaxis:{title:{text:"s12 [GeV²]"}},yaxis:{title:{text:"s13 [GeV²]"}}}}
        config={{responsive:true}} style={{width:"100%",height:"560px"}} useResizeHandler/></section>
      <section className="projections">{(["s12","s13","s23"] as const).map((key)=><div className="panel" key={key}><h2>{key} projection</h2>
        <Plot data={[{x:arrays[key],y:arrays.weights,type:"histogram",histfunc:"sum",nbinsx:70}]}
          layout={{autosize:true,margin:{l:55,r:15,t:15,b:50},xaxis:{title:{text:`${key} [GeV²]`}},yaxis:{title:{text:"Weighted yield"}}}}
          config={{responsive:true}} style={{width:"100%",height:"300px"}} useResizeHandler/></div>)}</section></>}
  </main>;
}

function Field(props:{label:string;value:string;onChange:(value:string)=>void}) {
  return <label>{props.label}<input value={props.value} onChange={(e)=>props.onChange(e.target.value)} required/></label>;
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App/></React.StrictMode>);
