import React, { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import Plot from "react-plotly.js";
import "./style.css";

type ParticleInfo = { name:string; pdgid:number; mass_gev:number; charge:number|null; spin:number|null; width_gev:number|null };
type SuggestedResonance = { name:string; pdgid:number; pair:"12"|"13"|"23"; mass_gev:number|null; width_gev:number|null; spin:number|null };
type ResonanceConfig = { id:string; component_type:"resonant"|"nonresonant"; name:string; pair:"12"|"13"|"23"; spin:number; mass:number; width:number; lineshape:"RBW"; magnitude:number; phase_deg:number; resonance_radius:number; mother_radius:number; source:"suggested" };
type DecayValidation = { allowed:boolean; channel:string; message:string; warnings:string[]; transition_count:number; suggested_resonances:Record<"12"|"13"|"23",SuggestedResonance[]> };
type ComponentNormalization = { key:string; integral:number; amplitude_scale:number };
type FitFraction = { key:string; fraction:number; percent:number };
type TheoreticalResponse = { s12_axis:number[]; s13_axis:number[]; intensity:(number|null)[][]; projection_s12:number[]; projection_s13:number[]; s23_axis:number[]; projection_s23:number[]; symmetrized:boolean; symmetry_term_count:number; component_normalizations:ComponentNormalization[]; fit_fractions:FitFraction[]; fit_fraction_sum:number };
type EventRow = { p1:[number,number,number,number]; p2:[number,number,number,number]; p3:[number,number,number,number]; s12:number; s13:number; s23:number; phase_space_weight:number; amplitude_real:number; amplitude_imag:number; amplitude_squared:number; total_weight:number };
type ToyResponse = { mother:ParticleInfo; daughters:[ParticleInfo,ParticleInfo,ParticleInfo]; unit:"GeV"; symmetrized:boolean; symmetry_term_count:number; components_normalized:boolean; component_normalizations:ComponentNormalization[]; events:EventRow[] };
type ModelFileAmplitude = { component_type?:"resonant"|"nonresonant"; name:string; pdgid:number|null; pair:"12"|"13"|"23"; lineshape:"RBW"; spin:number; mass_mev:number; width_mev:number; magnitude:number; phase_deg:number; resonance_radius_gev_inv:number; mother_radius_gev_inv:number; source:"suggested" };
type ModelFile = { schema_version:"1.0"; decay:{mother:string; daughters:[string,string,string]; symmetrize:boolean}; amplitudes:ModelFileAmplitude[]; plot:{resolution:number}; toy:{n_events:number; seed:number} };
type ModelImportValidation = { valid:boolean; allowed:boolean; channel:string; warnings:string[] };

const API_URL=import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
const pairTuple:Record<"12"|"13"|"23",[number,number]>={"12":[1,2],"13":[1,3],"23":[2,3]};

function App(){
  const [mother,setMother]=useState("D0"),[d1,setD1]=useState("pi+"),[d2,setD2]=useState("pi-"),[d3,setD3]=useState("pi0");
  const [plotResolution,setPlotResolution]=useState(140),[validationNonce,setValidationNonce]=useState(0);
  const [pendingImport,setPendingImport]=useState<ModelFile|null>(null),[modelMessage,setModelMessage]=useState<string|null>(null);
  const importInputRef=useRef<HTMLInputElement|null>(null);
  const [validation,setValidation]=useState<DecayValidation|null>(null),[validationKey,setValidationKey]=useState<string|null>(null),[validating,setValidating]=useState(false),[validationError,setValidationError]=useState<string|null>(null);
  const [resonances,setResonances]=useState<ResonanceConfig[]>([]);
  const [theory,setTheory]=useState<TheoreticalResponse|null>(null),[theoryLoading,setTheoryLoading]=useState(false),[theoryError,setTheoryError]=useState<string|null>(null);
  const [dalitzView,setDalitzView]=useState<"2d"|"3d">("2d");
  const [nEvents,setNEvents]=useState(10000),[seed,setSeed]=useState(7),[toy,setToy]=useState<ToyResponse|null>(null),[toyLoading,setToyLoading]=useState(false),[toyError,setToyError]=useState<string|null>(null),[exporting,setExporting]=useState<"csv"|null>(null);

  useEffect(()=>{
    const controller=new AbortController();
    const requestKey=JSON.stringify([mother,d1,d2,d3]);
    const timer=window.setTimeout(async()=>{
      setValidating(true);
      setValidation(null);
      setValidationKey(null);
      setValidationError(null);
      setResonances([]);
      setTheory(null);
      setToy(null);
      try{
        const response=await fetch(`${API_URL}/decays/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mother:{name:mother},daughters:[{name:d1},{name:d2},{name:d3}]}),signal:controller.signal});
        const payload=await response.json();
        if(!response.ok)throw new Error(payload.detail??"Decay validation failed.");
        setValidation(payload);
        setValidationKey(requestKey);
      }catch(error){
        if(error instanceof DOMException&&error.name==="AbortError")return;
        setValidationError(error instanceof Error?error.message:"Unexpected validation error.");
      }finally{
        if(!controller.signal.aborted)setValidating(false);
      }
    },400);
    return()=>{controller.abort();window.clearTimeout(timer)};
  },[mother,d1,d2,d3,validationNonce]);

  const modelPayload=useMemo(()=>({mother:{name:mother},daughters:[{name:d1},{name:d2},{name:d3}],symmetrize:true,normalize_components:true,resonances:resonances.map(({id:_id,pair,...item})=>({...item,pair:pairTuple[pair]}))}),[mother,d1,d2,d3,resonances]);
  const modelRevision=JSON.stringify(modelPayload);

  useEffect(()=>{if(!validation?.allowed)return;const controller=new AbortController();const timer=window.setTimeout(async()=>{setTheoryLoading(true);setTheoryError(null);try{const response=await fetch(`${API_URL}/model/theoretical-plot`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...modelPayload,resolution:plotResolution}),signal:controller.signal});const payload=await response.json();if(!response.ok)throw new Error(payload.detail??"Could not calculate theoretical plot.");setTheory(payload)}catch(error){if(error instanceof DOMException&&error.name==="AbortError")return;setTheory(null);setTheoryError(error instanceof Error?error.message:"Unexpected theoretical-plot error.")}finally{if(!controller.signal.aborted)setTheoryLoading(false)}},300);return()=>{controller.abort();window.clearTimeout(timer)}},[validation?.allowed,modelRevision,plotResolution]);

  useEffect(()=>{
    if(!pendingImport||!validation?.allowed)return;
    const importedChannelKey=JSON.stringify([pendingImport.decay.mother,...pendingImport.decay.daughters]);
    if(validationKey!==importedChannelKey)return;
    const importedResonances:ResonanceConfig[]=pendingImport.amplitudes.map((item,index)=>({
      id:item.component_type==="nonresonant"?"nonresonant":`${item.pair}:${item.pdgid??`imported-${index}`}`,
      component_type:item.component_type??"resonant",
      name:item.name,
      pair:item.pair,
      spin:item.spin,
      mass:item.mass_mev/1000,
      width:item.width_mev/1000,
      lineshape:item.lineshape,
      magnitude:item.magnitude,
      phase_deg:item.phase_deg,
      resonance_radius:item.resonance_radius_gev_inv,
      mother_radius:item.mother_radius_gev_inv,
      source:"suggested",
    }));
    setResonances(importedResonances);
    setPlotResolution(pendingImport.plot.resolution);
    setNEvents(pendingImport.toy.n_events);
    setSeed(pendingImport.toy.seed);
    setPendingImport(null);
    setToy(null);
    setModelMessage(`Model imported: ${validation.channel}`);
  },[pendingImport,validation,validationKey]);

  function exportModel(){
    const suggestedById=new Map<string,SuggestedResonance>();
    if(validation){
      (["12","13","23"] as const).forEach(pair=>validation.suggested_resonances[pair].forEach(item=>suggestedById.set(`${pair}:${item.pdgid}`,item)));
    }
    const modelDocument:ModelFile={
      schema_version:"1.0",
      decay:{mother,daughters:[d1,d2,d3],symmetrize:true},
      amplitudes:resonances.map(item=>({
        component_type:item.component_type,
        name:item.name,
        pdgid:suggestedById.get(item.id)?.pdgid??null,
        pair:item.pair,
        lineshape:item.lineshape,
        spin:item.spin,
        mass_mev:item.mass*1000,
        width_mev:item.width*1000,
        magnitude:item.magnitude,
        phase_deg:item.phase_deg,
        resonance_radius_gev_inv:item.resonance_radius,
        mother_radius_gev_inv:item.mother_radius,
        source:"suggested",
      })),
      plot:{resolution:plotResolution},
      toy:{n_events:nEvents,seed},
    };
    const blob=new Blob([JSON.stringify(modelDocument,null,2)],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const anchor=document.createElement("a");
    anchor.href=url;
    anchor.download=`${mother}_${d1}_${d2}_${d3}_dalitz_model.json`.replaceAll("/","_");
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    setModelMessage("Model exported as JSON.");
  }

  async function importModel(event:ChangeEvent<HTMLInputElement>){
    const file=event.target.files?.[0];
    event.target.value="";
    if(!file)return;
    setModelMessage(null);
    try{
      const parsed=JSON.parse(await file.text()) as ModelFile;
      if(parsed.schema_version!=="1.0")throw new Error(`Unsupported schema version: ${String(parsed.schema_version)}`);
      if(!parsed.decay||!Array.isArray(parsed.decay.daughters)||parsed.decay.daughters.length!==3)throw new Error("Invalid decay definition in model file.");
      if(!Array.isArray(parsed.amplitudes))throw new Error("Invalid amplitudes list in model file.");
      const response=await fetch(`${API_URL}/model/validate-import`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(parsed)});
      const result=await response.json() as ModelImportValidation & {detail?:string};
      if(!response.ok)throw new Error(result.detail??"Model validation failed.");
      if(!result.allowed)throw new Error(`The imported channel is not allowed: ${result.channel}`);
      setPendingImport(parsed);
      setMother(parsed.decay.mother);
      setD1(parsed.decay.daughters[0]);
      setD2(parsed.decay.daughters[1]);
      setD3(parsed.decay.daughters[2]);
      setValidationNonce(value=>value+1);
      setModelMessage(result.warnings.length?`Model accepted with warnings: ${result.warnings.join(" ")}`:"Model validated. Rebuilding the interface…");
    }catch(error){
      setModelMessage(error instanceof Error?`Import failed: ${error.message}`:"Import failed.");
    }
  }

  function toggleResonance(item:SuggestedResonance){const id=`${item.pair}:${item.pdgid}`;setResonances(current=>current.some(r=>r.id===id)?current.filter(r=>r.id!==id):(item.mass_gev==null||item.width_gev==null||item.width_gev<=0?current:[...current,{id,component_type:"resonant",name:item.name,pair:item.pair,spin:Math.round(item.spin??0),mass:item.mass_gev,width:item.width_gev,lineshape:"RBW",magnitude:1,phase_deg:0,resonance_radius:1.5,mother_radius:5,source:"suggested"}]))}

  function toggleNonResonant(){
    setResonances(current=>current.some(item=>item.component_type==="nonresonant")
      ? current.filter(item=>item.component_type!=="nonresonant")
      : [...current,{id:"nonresonant",component_type:"nonresonant",name:"Non-resonant",pair:"12",spin:0,mass:1,width:1,lineshape:"RBW",magnitude:1,phase_deg:0,resonance_radius:1.5,mother_radius:5,source:"suggested"}]);
  }
  function updateResonance(
    id:string,
    field:"magnitude"|"phase_deg"|"mass"|"width"|"resonance_radius"|"mother_radius",
    value:number,
  ){
    setResonances(current=>current.map(item=>item.id===id?{...item,[field]:value}:item))
  }
  function resetResonance(id:string){
    setResonances(current=>current.map(item=>{
      if(item.id!==id)return item;
      if(item.component_type==="nonresonant")return {...item,magnitude:1,phase_deg:0};
      const suggested=validation?.suggested_resonances[item.pair]?.find(candidate=>`${item.pair}:${candidate.pdgid}`===id);
      return {...item,mass:suggested?.mass_gev??item.mass,width:suggested?.width_gev??item.width,magnitude:1,phase_deg:0,resonance_radius:1.5,mother_radius:5};
    }))
  }

  async function generateToy(event:FormEvent){event.preventDefault();if(!validation?.allowed)return;setToyLoading(true);setToyError(null);try{const response=await fetch(`${API_URL}/toy/generate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...modelPayload,n_events:nEvents,seed})});const payload=await response.json();if(!response.ok)throw new Error(payload.detail??"Could not generate toy sample.");setToy(payload)}catch(error){setToy(null);setToyError(error instanceof Error?error.message:"Unexpected toy-generation error.")}finally{setToyLoading(false)}}

  async function download(format:"csv"){setExporting(format);setToyError(null);try{const response=await fetch(`${API_URL}/toy/export/${format}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...modelPayload,n_events:nEvents,seed})});if(!response.ok){const payload=await response.json();throw new Error(payload.detail??"Export failed.")}const blob=await response.blob();const url=URL.createObjectURL(blob);const anchor=document.createElement("a");anchor.href=url;anchor.download=`dalitz_toy.${format}`;document.body.appendChild(anchor);anchor.click();anchor.remove();URL.revokeObjectURL(url)}catch(error){setToyError(error instanceof Error?error.message:"Unexpected export error.")}finally{setExporting(null)}}

  const toyArrays=useMemo(()=>{const events=toy?.events??[];return{s12:events.map(e=>e.s12),s13:events.map(e=>e.s13),s23:events.map(e=>e.s23),weights:events.map(e=>e.total_weight),intensity:events.map(e=>e.amplitude_squared)}},[toy]);
  const fitFractionByIndex=useMemo(()=>new Map((theory?.fit_fractions??[]).map(item=>[Number(item.key.split(":",1)[0]),item.percent])),[theory]);

  return <main><header><div className="header-top"><div><p className="eyebrow">Three-body decay playground</p><h1>Dalitz Plot Web Visualizer</h1></div><div className="model-actions"><button type="button" className="secondary" onClick={exportModel}>Export model</button><button type="button" onClick={()=>importInputRef.current?.click()}>Import model</button><input ref={importInputRef} className="visually-hidden" type="file" accept="application/json,.json" onChange={importModel}/></div></div><p className="lead">The mathematical model updates continuously. Toy Monte Carlo samples are generated only on request.</p>{modelMessage&&<p className="model-message">{modelMessage}</p>}</header>
    <section className="panel"><div className="section-heading"><div><h2>Decay channel</h2><p>Automatically checked with qrules.</p></div><span className="badge">GeV units</span></div><div className="grid particles-grid"><Field label="Mother" value={mother} onChange={setMother}/><Field label="Daughter 1" value={d1} onChange={setD1}/><Field label="Daughter 2" value={d2} onChange={setD2}/><Field label="Daughter 3" value={d3} onChange={setD3}/></div><div className={`validation-box ${validation?.allowed?"allowed":"forbidden"}`}>{validating&&<strong>Checking with qrules…</strong>}{validationError&&<strong>{validationError}</strong>}{validation&&<><strong>{validation.allowed?"✓ Allowed decay":"✕ Decay not allowed"}</strong><span>{validation.message}</span>{validation.allowed&&<span>{validation.transition_count} allowed transitions found.</span>}</>}</div></section>

    {validation?.allowed&&<section className="panel"><div className="section-heading"><div><h2>Resonance model</h2><p>Select suggested states and edit their coefficient and complete dynamic-RBW parameters.</p></div><span className="badge">{resonances.length} selected</span></div><div className="resonance-columns">{(["12","13","23"] as const).map(pair=><article key={pair}><h3>Pair {pair}</h3>{validation.suggested_resonances[pair].length===0?<p className="muted">No suggested states.</p>:<ul>{validation.suggested_resonances[pair].map(item=>{const id=`${pair}:${item.pdgid}`,selected=resonances.some(r=>r.id===id),enabled=item.mass_gev!=null&&item.width_gev!=null&&item.width_gev>0;return <li key={id} className={selected?"selected":""}><label className="resonance-choice"><input type="checkbox" checked={selected} disabled={!enabled} onChange={()=>toggleResonance(item)}/><span><strong>{item.name}</strong><small>{item.mass_gev!=null?(item.mass_gev*1000).toFixed(2):"?"} MeV · Γ {item.width_gev!=null?(item.width_gev*1000).toFixed(2):"?"} MeV</small></span></label></li>})}</ul>}</article>)}</div><div className="nonresonant-control"><label className="resonance-choice"><input type="checkbox" checked={resonances.some(item=>item.component_type==="nonresonant")} onChange={toggleNonResonant}/><span><strong>Non-resonant term</strong><small>Constant scalar amplitude over phase space</small></span></label></div>{resonances.length>0&&<div className="selected-model"><h3>Selected amplitudes</h3><p className="muted">Each complete symmetrized contribution is normalized before its coefficient is applied. Fit-fraction sum: {theory?`${(100*theory.fit_fraction_sum).toFixed(2)}%`:"—"}; it need not equal 100% because of interference.</p>{resonances.map((r,index)=><div className="resonance-editor" key={r.id}><div><strong>{r.name}</strong><span>{r.component_type==="nonresonant"?"constant scalar amplitude":`pair ${r.pair} · spin ${r.spin} · dynamic RBW`}</span><span className="fit-fraction">Fit fraction: {theoryLoading?"updating…":`${(fitFractionByIndex.get(index)??0).toFixed(2)}%`}</span></div><label>Magnitude<input type="number" step="0.05" min="0" value={r.magnitude} onChange={e=>updateResonance(r.id,"magnitude",Number(e.target.value))}/></label><label>Phase [deg]<input type="number" step="1" value={r.phase_deg} onChange={e=>updateResonance(r.id,"phase_deg",Number(e.target.value))}/></label>{r.component_type==="resonant"&&<><label>Pole mass [MeV]<input type="number" min="0.001" step="0.1" value={r.mass*1000} onChange={e=>updateResonance(r.id,"mass",Number(e.target.value)/1000)}/></label><label>Pole width [MeV]<input type="number" min="0.001" step="0.1" value={r.width*1000} onChange={e=>updateResonance(r.id,"width",Number(e.target.value)/1000)}/></label><label>Spin / orbital L<input type="number" value={r.spin} readOnly disabled title="Fixed by particle/qrules"/></label><label>Resonance radius [GeV⁻¹]<input type="number" min="0.01" step="0.1" value={r.resonance_radius} onChange={e=>updateResonance(r.id,"resonance_radius",Number(e.target.value))}/></label><label>Mother radius [GeV⁻¹]<input type="number" min="0.01" step="0.1" value={r.mother_radius} onChange={e=>updateResonance(r.id,"mother_radius",Number(e.target.value))}/></label></>}<button type="button" className="secondary" onClick={()=>resetResonance(r.id)}>Reset to default</button></div>)}</div>}</section>}

    {validation?.allowed&&<section className="panel plot-panel"><div className="section-heading"><div><h2>Theoretical model</h2><p>Continuous evaluation of |A(s₁₂,s₁₃)|² on the physical Dalitz region.</p></div><div className="theory-controls"><label>Grid resolution<input type="number" min={40} max={350} step={10} value={plotResolution} onChange={e=>setPlotResolution(Number(e.target.value))}/></label><label>Dalitz view<select value={dalitzView} onChange={e=>setDalitzView(e.target.value as "2d"|"3d")}><option value="2d">2D heatmap</option><option value="3d">3D surface</option></select></label><span className="badge">{theoryLoading?"Updating…":"Automatic"}</span></div></div>{theoryError&&<p className="error">{theoryError}</p>}{theory&&<>{dalitzView==="2d"?<Plot data={[{x:theory.s12_axis,y:theory.s13_axis,z:theory.intensity,type:"heatmap",colorscale:"Viridis",colorbar:{title:{text:"|A|²"}},hovertemplate:"s12=%{x:.4f}<br>s13=%{y:.4f}<br>|A|²=%{z:.4g}<extra></extra>"}]} layout={{autosize:true,margin:{l:65,r:40,t:20,b:55},xaxis:{title:{text:"s12 [GeV²]"}},yaxis:{title:{text:"s13 [GeV²]"}}}} config={{responsive:true}} style={{width:"100%",height:"560px"}} useResizeHandler/>:<Plot data={[{x:theory.s12_axis,y:theory.s13_axis,z:theory.intensity,type:"surface",colorscale:"Viridis",colorbar:{title:{text:"|A|²"}},hovertemplate:"s12=%{x:.4f}<br>s13=%{y:.4f}<br>|A|²=%{z:.4g}<extra></extra>"}]} layout={{autosize:true,margin:{l:10,r:10,t:20,b:10},scene:{xaxis:{title:{text:"s12 [GeV²]"}},yaxis:{title:{text:"s13 [GeV²]"}},zaxis:{title:{text:"|A|²"}},camera:{eye:{x:1.5,y:1.5,z:1.1}}}}} config={{responsive:true}} style={{width:"100%",height:"650px"}} useResizeHandler/>}<div className="projections theoretical-projections"><TheoryProjection axis={theory.s12_axis} values={theory.projection_s12} label="s12"/><TheoryProjection axis={theory.s13_axis} values={theory.projection_s13} label="s13"/><TheoryProjection axis={theory.s23_axis} values={theory.projection_s23} label="s23"/></div></>}</section>}

    {validation?.allowed&&<form className="panel" onSubmit={generateToy}><div className="section-heading"><div><h2>Toy Monte Carlo</h2><p>Generate a finite weighted sample with phasespace. A second Dalitz plot and three histograms will appear below.</p></div><span className="badge">Optional</span></div><div className="grid generation-grid"><label>Events<input type="number" min={1} max={1_000_000} value={nEvents} onChange={e=>setNEvents(Number(e.target.value))}/></label><label>Seed<input type="number" value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label><button type="submit" disabled={toyLoading}>{toyLoading?"Generating…":"Generate Toy"}</button></div>{toyError&&<p className="error">{toyError}</p>}</form>}

    {toy&&<><section className="panel plot-panel"><div className="section-heading"><div><h2>Generated toy sample</h2><p>Event cloud from phasespace, weighted with wPS|A|².</p></div><div className="download-actions"><button type="button" disabled={exporting!==null} onClick={()=>download("csv")}>{exporting==="csv"?"Preparing CSV…":"Download CSV"}</button></div></div><Plot data={[{x:toyArrays.s12,y:toyArrays.s13,mode:"markers",type:"scattergl",marker:{size:5,opacity:.65,color:toyArrays.intensity,colorscale:"Viridis",showscale:true,colorbar:{title:{text:"|A|²"}}},text:toyArrays.s23.map((v,i)=>`s23=${v.toFixed(4)} GeV²<br>weight=${toyArrays.weights[i].toExponential(3)}`),hovertemplate:"s12=%{x:.4f}<br>s13=%{y:.4f}<br>%{text}<extra></extra>"}]} layout={{autosize:true,margin:{l:65,r:40,t:20,b:55},xaxis:{title:{text:"s12 [GeV²]"}},yaxis:{title:{text:"s13 [GeV²]"}}}} config={{responsive:true}} style={{width:"100%",height:"560px"}} useResizeHandler/></section><section className="projections">{(["s12","s13","s23"] as const).map(key=><div className="panel" key={key}><h2>{key} toy histogram</h2><Plot data={[{x:toyArrays[key],y:toyArrays.weights,type:"histogram",histfunc:"sum",nbinsx:70}]} layout={{autosize:true,margin:{l:55,r:15,t:15,b:50},xaxis:{title:{text:`${key} [GeV²]`}},yaxis:{title:{text:"Weighted yield"}}}} config={{responsive:true}} style={{width:"100%",height:"300px"}} useResizeHandler/></div>)}</section></>}
  </main>
}

function Field({label,value,onChange}:{label:string;value:string;onChange:(value:string)=>void}){return <label>{label}<input value={value} onChange={e=>onChange(e.target.value)} required/></label>}
function TheoryProjection({axis,values,label}:{axis:number[];values:number[];label:string}){return <div className="projection-card"><h3>{label} theoretical projection</h3><Plot data={[{x:axis,y:values,type:"scatter",mode:"lines"}]} layout={{autosize:true,margin:{l:55,r:15,t:15,b:50},xaxis:{title:{text:`${label} [GeV²]`}},yaxis:{title:{text:"Integrated intensity"}}}} config={{responsive:true}} style={{width:"100%",height:"300px"}} useResizeHandler/></div>}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App/></React.StrictMode>);
